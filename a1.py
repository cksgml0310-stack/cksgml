import streamlit as st
import pandas as pd
from datetime import datetime

# --- Google Spreadsheet CSV URL ---
CSV_URL = "https://docs.google.com/spreadsheets/d/1KsUha1HNcJApfUNlqsr57rQbgvA7lAsmpPcZ7nF48GI/gviz/tq?tqx=out:csv&sheet=Sheet1"

# --- Load data ---
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    required_cols = {"date", "category", "theme", "title", "source"}
    if not required_cols.issubset(df.columns):
        st.error(f"❌ 필수 컬럼이 누락되었습니다: {required_cols - set(df.columns)}")
        return pd.DataFrame()

    # 날짜 형식 변환
    try:
        df["date"] = pd.to_datetime(df["date"].str.strip('"') + " 2025", format="%a, %d %b %Y")
    except Exception as e:
        st.error("❌ 날짜 형식 오류:")
        st.exception(e)
        return pd.DataFrame()
    
    return df

# --- Load ---
df = load_data()
if df.empty:
    st.stop()

# --- Header ---
st.title("🗞️ 오늘의 뉴스 대시보드")
st.markdown(f"📅 오늘 날짜: `{datetime.now().strftime('%Y-%m-%d')}`")
st.markdown("---")

# --- 날짜 슬라이더 필터 (수정 완료) ---
min_date = df["date"].min().to_pydatetime()
max_date = df["date"].max().to_pydatetime()

start_date, end_date = st.slider(
    "🗓️ 날짜 범위 선택",
    min_value=min_date,
    max_value=max_date,
    value=(max_date, max_date),
    format="YYYY-MM-DD"
)

df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

# --- 카테고리 필터 ---
all_categories = sorted(df["category"].dropna().unique())
selected_categories = st.multiselect("📚 카테고리 필터", all_categories, default=all_categories)
df = df[df["category"].isin(selected_categories)]

# --- 테마 필터 ---
themes = df["theme"].dropna().unique()
selected_theme = st.selectbox("🎨 테마 선택 (선택 안 해도 됨)", ["전체 보기"] + list(themes))
if selected_theme != "전체 보기":
    df = df[df["theme"] == selected_theme]

# --- 기사 출력 ---
for category in selected_categories:
    cat_df = df[df["category"] == category]
    if cat_df.empty:
        continue

    with st.expander(f"📚 {category} ({len(cat_df)}건)", expanded=True):
        for _, row in cat_df.iterrows():
            st.markdown(f"### {row['title']}")
            st.markdown(f"- 🗞 **{row['source']}**")
            st.markdown(f"- 📌 {row.get('summary', '요약 없음')}")
            if pd.notna(row.get("url")) and row["url"].strip() != "":
                st.markdown(f"[🔗 출처 보기]({row['url']})")
            st.markdown("---")
