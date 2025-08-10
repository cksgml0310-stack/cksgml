import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 구글 스프레드시트 인증 설정
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)

# 시트 열기
sheet = gc.open("Cnerge").worksheet("시트1")

# 데이터 가져오기
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 날짜 열 전처리: "Sun, 03 Aug" → datetime 객체로 변환
df["date"] = df["date"].apply(lambda x: datetime.strptime(x.strip('"') + " 2025", "%a, %d %b %Y"))

# Streamlit 앱 제목
st.title("🗞️ AI 뉴스 아카이브")

# 날짜 선택 위젯 (최신 날짜가 먼저 나오도록 정렬)
dates = sorted(df["date"].unique(), reverse=True)
selected_date = st.selectbox("📅 날짜 선택", dates, format_func=lambda d: d.strftime("%Y-%m-%d"))

# 선택된 날짜의 뉴스만 필터링
filtered_df = df[df["date"] == selected_date]

# 카테고리별로 뉴스 분류
categories = filtered_df["category"].unique()

for category in categories:
    with st.expander(f"📂 {category} ({(filtered_df['category'] == category).sum()}개)", expanded=True):
        category_df = filtered_df[filtered_df["category"] == category]
        for _, row in category_df.iterrows():
            st.markdown(f"### {row['title']}")
            st.markdown(f"- 🗞 **{row['source']}**")
            st.markdown(f"- 📌 {row['summary']}")
            st.markdown(f"[🔗 출처 보기]({row['url']})", unsafe_allow_html=True)
            st.markdown("---")
