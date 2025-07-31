import streamlit as st
import pandas as pd
from datetime import datetime

st.title("📰 오늘의 AI 뉴스")
today = datetime.now().strftime("%Y년 %m월 %d일")
st.markdown(f"#### 📅 {today}")

uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    categories = sorted(df['category'].unique())

    for category in categories:
        st.header(f"📂 {category}")
        filtered = df[df['category'] == category]

        for _, article in filtered.iterrows():
            with st.expander(f"{article['title']} ({article['source']})"):
                st.write(article['summary'])
                st.markdown(f"[🔗 기사 링크]({article['url']})")
else:
    st.info("위에서 articles.xlsx 파일을 업로드해주세요.")