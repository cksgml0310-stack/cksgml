import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="AI 뉴스 대시보드", layout="wide")

# ✅ Google 인증: credentials.json 파일 직접 불러오기
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_path = "credentials.json"  # ← 여기만 바뀜

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"❌ 인증 실패: {e}")
    st.stop()

# 📄 Google Sheet 열기
SHEET_NAME = st.text_input("📎 불러올 구글 시트 이름:", "article")
try:
    sheet = client.open(SHEET_NAME).worksheet("article")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    st.success("✅ Google Sheet에서 데이터 불러오기 성공")
except Exception as e:
    st.error(f"❌ 시트 불러오기 실패: {e}")
    st.stop()

# 🗓 오늘 날짜 표시
st.title("📰 AI 뉴스 대시보드")
st.markdown(f"📅 오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
st.markdown("---")

# ✅ theme 선택 및 필터링
if "theme" not in df.columns:
    st.error("❌ 'theme' 컬럼이 없습니다. 구글 시트에 'theme' 열이 있는지 확인하세요.")
    st.stop()

themes = df["theme"].dropna().unique().tolist()
selected_theme = st.radio("🎯 보고 싶은 주제를 선택하세요", themes)

filtered_df = df[df["theme"] == selected_theme]

# 📂 선택된 theme 내에서 category별 뉴스 정리
if "category" not in filtered_df.columns:
    st.error("❌ 'category' 컬럼이 없습니다. 구글 시트의 포맷을 확인해주세요.")
    st.stop()

categories = filtered_df["category"].dropna().unique()

for category in categories:
    st.subheader(f"📂 {category}")
    category_df = filtered_df[filtered_df["category"] == category]

    for idx, row in category_df.iterrows():
        with st.expander(f"📰 {row.get('title', '제목 없음')} ({row.get('source', '출처 없음')})"):
            st.markdown(f"**요약:** {row.get('summary', '요약 없음')}")
            if pd.notna(row.get("url")) and row.get("url") != "":
                st.markdown(f"[🔗 기사 보기]({row['url']})")
