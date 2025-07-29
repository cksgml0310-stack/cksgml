import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AI 뉴스 대시보드", layout="wide")

st.title("📰 AI 뉴스 대시보드")
st.markdown(f"📅 **오늘 날짜:** {datetime.now().strftime('%Y년 %m월 %d일')}")  
st.markdown("---")

uploaded_file = st.file_uploader("📂 엑셀 파일을 업로드 해주세요 (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ 파일 불러오기 성공!")

        # 컬럼명 출력 (디버깅용)
        st.write("데이터프레임 컬럼명:", df.columns.tolist())

        # 'category' 컬럼이 있는지 확인
        if "category" not in df.columns:
            st.error("❌ 'category' 컬럼이 없습니다. 엑셀 파일을 확인해주세요.")
        else:
            categories = df["category"].unique()
            for category in categories:
                st.subheader(f"📂 {category}")
                category_df = df[df["category"] == category]

                for idx, row in category_df.iterrows():
                    with st.expander(f"📰 {row.get('title', '제목 없음')} ({row.get('source', '출처 없음')})"):
                        st.write(f"**요약:** {row.get('summary', '요약 없음')}")
                        url = row.get('url', '')
                        if url:
                            st.markdown(f"[🔗 출처 보기]({url})")
                        else:
                            st.write("출처 URL이 없습니다.")
    except Exception as e:
        st.error(f"❌ 파일을 읽는 중 오류 발생: {e}")
else:
    st.info("엑셀 파일을 업로드해주세요.")