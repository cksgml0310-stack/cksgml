import streamlit as st
import pandas as pd
from datetime import datetime

# --- 구글 스프레드시트 CSV URL ---
CSV_URL = "https://docs.google.com/spreadsheets/d/1KsUha1HNcJApfUNlqsr57rQbgvA7lAsmpPcZ7nF48GI/gviz/tq?tqx=out:csv&sheet=Sheet1"

# --- 데이터 불러오기 ---
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()  # 컬럼명 공백 제거
    if "date" not in df.columns or "theme" not in df.columns or "category" not in df.columns:
        st.error("필수 컬럼이 누락되었습니다.")
        st.write(df.head())
        return pd.DataFrame()
    try:
        df["date"] = pd.to_datetime(df["date"].str.strip('"') + " 2025", format="%a, %d %b %Y")
    except Exception as e:
        st.error("날짜 포맷 오류 발생")
        st.exception(e)
        return pd.DataFrame()
    return df

df = load_data()

if df.empty:
    st.stop()

# --- 오늘 날짜 표시 ---
st.title("🗞️ 오늘의 뉴스")
st.markdown(f"📅 오늘 날짜: {datetime.now().strftime('%Y-%m-%d')}")
st.markdown("---")

# --- theme별 버튼으로 필터 선택 ---
themes = df["theme"].dropna().unique()
selected_theme = None

st.markdown("### 🗂 테마 선택")
cols = st.columns(len(themes))
for i, theme in enumerate(themes):
    if cols[i].button(theme):
        selected_theme = theme

# theme 필터링
if selected_theme:
    df = df[df["theme"] == selected_theme]

# --- 날짜 선택박스 ---
dates = sorted(df["date"].unique(), reverse=True)
selected_date = st.selectbox("📅 날짜 선택", dates, format_func=lambda d: d.strftime("%Y-%m-%d"))
df = df[df["date"] == selected_date]

# --- category별 뉴스 출력 ---
categories = df["category"].dropna().unique()

for category in categories:
    with st.expander(f"📚 {category} ({(df['category'] == category).sum()}건)", expanded=True):
        cat_df = df[df["category"] == category]
        for _, row in cat_df.iterrows():
            st.markdown(f"### {row['title']}")
            st.markdown(f"- 🗞 **{row['source']}**")
            st.markdown(f"- 📌 {row.get('summary', '요약 없음')}")
            if pd.notna(row.get("url")) and row["url"] != "":
                st.markdown(f"[🔗 출처 보기]({row['url']})")
            st.markdown("---")
