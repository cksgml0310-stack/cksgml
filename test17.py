import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 구글 시트 인증 및 데이터 불러오기 ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)

sheet = gc.open("article").sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- 날짜 처리 ---
df["date"] = df["date"].apply(lambda x: datetime.strptime(x.strip('"') + " 2025", "%a, %d %b %Y"))

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
