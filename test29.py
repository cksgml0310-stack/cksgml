import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# --- 페이지 설정 ---
st.set_page_config(layout="wide")

# --- CSS 스타일 적용 (iframe 너비 강제 적용) ---
st.markdown("""
    <style>
        body {
            background-color: #f7f7f7;
            font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Nanum Gothic', sans-serif;
        }
        .stButton>button {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e6e6e6;
            border-radius: 5px;
        }
        .stMultiSelect div[data-baseweb="select"] {
            border-color: #e6e6e6;
        }
        .stTextInput div[data-baseweb="input"] {
            border-color: #e6e6e6;
        }

        /* iframe 부모 컨테이너의 가로 너비를 100%로 설정 */
        div[data-testid="stExpander"] > div > div {
            width: 100% !important;
        }
        /* iframe 자체의 가로 너비를 100%로 설정 */
        iframe {
            width: 100% !important;
            border: 1px solid #e6e6e6;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 구글 스프레드시트 CSV URL ---
CSV_URL = "https://docs.google.com/spreadsheets/d/14I9HkPiBhKs6nXLt6kEBalQHeasrwINWshFDghTHbZE/gviz/tq?tqx=out:csv&sheet=Sheet1"

# --- 데이터 불러오기 ---
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    required_cols = {"date", "category", "theme", "title", "source"}
    if not required_cols.issubset(df.columns):
        st.error(f"필수 컬럼 누락: {required_cols - set(df.columns)}")
        return pd.DataFrame()
    try:
        df["date"] = pd.to_datetime(df["date"].str.strip('"') + " 2025", format="%a, %d %b %Y")
    except Exception as e:
        st.error("날짜 포맷 오류 발생. 스프레드시트의 날짜 형식을 확인하세요.")
        st.exception(e)
        return pd.DataFrame()
    return df

df = load_data()

if df.empty:
    st.stop()

# --- 제목 및 오늘 날짜 표시 ---
st.title("📰 SK networks 뉴스")
st.markdown(f"### 📅 오늘 날짜: {datetime.now().strftime('%Y-%m-%d')}")
st.markdown("---")

# --- 필터 영역 (2개의 컬럼으로 분할, 비율 1:1) ---
filter_col1, filter_col2 = st.columns(2)

# 1. 테마 필터 (멀티셀렉트)
with filter_col1:
    all_themes = sorted(df["theme"].dropna().unique())
    selected_themes = st.multiselect("🏷️ 테마 선택", all_themes, default=all_themes)

# 2. 날짜 필터 (달력 위젯)
with filter_col2:
    valid_dates = df["date"].dropna()
    if not valid_dates.empty:
        min_data_date = valid_dates.min().date()
        max_data_date = valid_dates.max().date()
    else:
        min_data_date = datetime.now().date()
        max_data_date = datetime.now().date()
    
    # 시작일과 종료일을 한 줄에 나란히 배치
    date_start_col, date_end_col = st.columns(2)
    with date_start_col:
        start_date = st.date_input(
            "🗓️ 시작일",
            value=min_data_date,
            min_value=min_data_date,
            max_value=max_data_date
        )
    with date_end_col:
        end_date = st.date_input(
            "🗓️ 종료일",
            value=max_data_date,
            min_value=start_date,
            max_value=max_data_date
        )

# --- 검색 기능 ---
search_query = st.text_input("🔍 키워드 검색", placeholder="제목 또는 요약에 포함된 키워드를 입력하세요.")

# --- 필터링 로직 ---
filtered_df = df.copy()
filtered_by_date = False
filtered_by_keyword = False

if selected_themes:
    filtered_df = filtered_df[filtered_df["theme"].isin(selected_themes)]

if start_date and end_date:
    filtered_df = filtered_df[
        (filtered_df["date"].dt.date >= start_date) & 
        (filtered_df["date"].dt.date <= end_date)
    ]
    if len(filtered_df) == 0:
        filtered_by_date = True

if search_query:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False) |
        filtered_df.get("summary", pd.Series(dtype='object')).str.contains(search_query, case=False, na=False)
    ]
    if len(filtered_df) == 0:
        filtered_by_keyword = True

# --- 뉴스 출력 ---
if not filtered_df.empty:
    categories = filtered_df["category"].dropna().unique()
    for category in categories:
        with st.expander(f"📚 {category} ({(filtered_df['category'] == category).sum()}건)", expanded=True):
            cat_df = filtered_df[filtered_df["category"] == category]
            for _, row in cat_df.iterrows():
                st.markdown(f"### 💡 {row['title']}")
                st.markdown(f"- 🏢 **{row['source']}** ({row['date'].strftime('%Y-%m-%d')})")
                st.markdown(f"- 📌 {row.get('summary', '요약 없음')}")
                if pd.notna(row.get("url")) and row["url"] != "":
                    st.markdown(f"[📖 본문 보기]({row['url']})")
                    with st.expander("🖼️ 미리보기", expanded=True):
                        components.html(
                            f'<iframe src="{row["url"]}" width="100%" height="300px"></iframe>',
                            height=300,
                            scrolling=True
                        )
                        st.info("미리보기가 보이지 않는다면, 해당 웹사이트에서 미리보기 기능을 지원하지 않는 것일 수 있습니다.")
                st.markdown("---")
else:
    st.markdown("### 😥 해당 뉴스 없음")
    if filtered_by_date:
        st.markdown("날짜를 다시 설정하세요")
    if filtered_by_keyword:
        st.markdown("키워드를 다시 설정하세요")