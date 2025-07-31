import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime

st.set_page_config(page_title="AI 뉴스 대시보드", layout="wide")

# 🎯 1. 가장 최신의 .xlsx 파일 찾기
def get_latest_excel_file():
    files = glob.glob("*.xlsx")  # 현재 폴더에서 .xlsx 파일 모두 찾기
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)  # 가장 최근 수정된 파일
    return latest_file

latest_file = get_latest_excel_file()

if latest_file:
    try:
        df = pd.read_excel(latest_file)
        st.success(f"✅ 파일 불러오기 성공: `{latest_file}`")
    except Exception as e:
        st.error(f"❌ 파일을 불러오는 중 오류 발생: {e}")
        st.stop()
else:
    st.warning("📁 .xlsx 파일이 현재 폴더에 없습니다. 같은 폴더에 올려주세요.")
    st.stop()

# 🎨 2. 상단 제목 영역
st.title("📰 AI 뉴스 대시보드")
st.markdown(f"📅 **오늘 날짜:** {datetime.now().strftime('%Y년 %m월 %d일')}")
st.markdown("---")

# 📊 3. 기사 카테고리별 표시
categories = df["category"].unique()

for category in categories:
    st.subheader(f"📂 {category}")
    category_df = df[df["category"] == category]

    for idx, row in category_df.iterrows():
        with st.expander(f"📰 {row['title']} ({row['source']})"):
            st.write(f"**요약:** {row['summary']}")
            st.markdown(f"[🔗 출처 보기]({row['url']})")