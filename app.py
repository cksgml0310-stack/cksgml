import streamlit as st
from datetime import datetime

# -------------------------
# 1. 상단 헤더
# -------------------------
st.title("📰 오늘의 AI 뉴스")
today = datetime.now().strftime("%Y년 %m월 %d일")
st.markdown(f"#### 📅 {today}")

# -------------------------
# 2. 기사 데이터 예시 (샘플)
# -------------------------
articles = [
    {
        "title": "AI가 창작한 그림, 예술인가 도구인가?",
        "source": "한겨레신문",
        "summary": "AI가 생성한 이미지가 실제 미술 시장에서 거래되면서 예술성과 윤리 문제를 둘러싼 논의가 뜨겁다.",
        "category": "AI와 예술",
        "url": "https://example.com/article1"
    },
    {
        "title": "AI 튜터, 초등학교 교실에 들어오다",
        "source": "조선일보",
        "summary": "AI 기반 학습 도우미가 초등학교에서 파일럿 수업을 시작했다. 교사들은 아직 회의적이지만 가능성은 높다고 본다.",
        "category": "AI와 교육",
        "url": "https://example.com/article2"
    },
    {
        "title": "AI 면접 시대, 기업이 원하는 인재상은?",
        "source": "동아일보",
        "summary": "대기업들이 AI 면접을 도입하면서 지원자들은 기술뿐 아니라 AI 알고리즘에 대한 이해도 필요해졌다.",
        "category": "AI와 채용",
        "url": "https://example.com/article3"
    },
    {
        "title": "AI 작곡 프로그램, 음반시장 진출",
        "source": "중앙일보",
        "summary": "AI가 작곡한 곡이 실제 가수의 앨범에 수록되어 주목을 받고 있다.",
        "category": "AI와 예술",
        "url": "https://example.com/article4"
    },
]

# -------------------------
# 3. 분류별 기사 정리 및 표시
# -------------------------
categories = sorted(set(article["category"] for article in articles))

for category in categories:
    st.header(f"📂 {category}")
    for article in [a for a in articles if a["category"] == category]:
        with st.expander(f"{article['title']} ({article['source']})"):
            st.write(article["summary"])
            st.markdown(f"[🔗 기사 링크]({article['url']})")