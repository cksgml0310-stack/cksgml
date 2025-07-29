import streamlit as st
import pandas as pd
import gdown
import os
from datetime import datetime

st.set_page_config(page_title="AI 뉴스 대시보드", layout="wide")

# 🔗 1. Google Drive 링크에서 파일 ID 추출
GDRIVE_URL = st.text_input("📎 Google Drive 링크를 입력하세요:",
                           "https://drive.google.com/file/d/파일_ID/view?usp=sharing")

def extract_file_id(gdrive_url):
    try:
        return gdrive_url.split("/d/")[1].split("/")[0]
    except:
        return None

file_id = extract_file_id(GDRIVE_URL)

if file_id:
    download_url = f"https://drive.google.com/uc?id={file_id}"
    output_file = "downloaded.xlsx"

    # 2. 다운로드 시도
    try:
        gdown.download(download_url, output_file, quiet=False)
        df = pd.read_excel(output_file, engine="openpyxl")
        st.success("✅ 파일 다운로드 및 불러오기 성공")
    except Exception as e:
        st.error(f"❌ 파일 다운로드 또는 읽기 실패: {e}")
        st.stop()
else:
    st.warning("📌 유효한 Google Drive 링크를 입력해주세요.")
    st.stop()

# 3. 날짜 표시
st.title("📰 AI 뉴스 대시보드")
st.markdown(f"📅 오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
st.markdown("---")

# 4. 카테고리별 뉴스 표시
if "category" not in df.columns:
    st.error("❌ 'category' 컬럼이 없습니다. 엑셀 포맷을 확인해주세요.")
    st.stop()

categories = df["category"].dropna().unique()

for category in categories:
    st.subheader(f"📂 {category}")
    category_df = df[df["category"] == category]

    for idx, row in category_df.iterrows():
        with st.expander(f"📰 {row.get('title', '제목 없음')} ({row.get('source', '출처 없음')})"):
            st.write(f"**요약:** {row.get('summary', '요약 없음')}")
            if pd.notna(row.get("url")):
                st.markdown(f"[🔗 기사 보기]({row['url']})")