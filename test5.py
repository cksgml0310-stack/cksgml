import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="AI 뉴스 대시보드", layout="wide")

# 1. 폴더에서 엑셀 파일 목록 불러오기
folder_path = "./"  # 현재 폴더 기준
excel_files = glob.glob(os.path.join(folder_path, "*.xlsx"))

st.title("📁 폴더 내 AI 뉴스 파일 대시보드")

if not excel_files:
    st.warning("❌ 현재 폴더에 `.xlsx` 파일이 없습니다. 파일을 먼저 업로드하거나 넣어주세요.")
    st.stop()

# 2. 사용자에게 파일 선택 옵션 제공
selected_file = st.selectbox("불러올 엑셀 파일을 선택하세요:", excel_files)

# 3. 파일 읽기
try:
    df = pd.read_excel(selected_file, engine="openpyxl")
    st.success(f"✅ `{os.path.basename(selected_file)}` 파일 불러오기 성공")
except Exception as e:
    st.error(f"❌ 파일을 읽는 중 오류 발생: {e}")
    st.stop()

# 4. 기본 정보 출력
st.markdown(f"📅 **파일 수정일:** {datetime.fromtimestamp(os.path.getmtime(selected_file)).strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# 5. 카테고리별 뉴스 보기
if "category" not in df.columns:
    st.error("❌ 이 파일에는 'category' 컬럼이 없습니다. 올바른 포맷인지 확인하세요.")
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