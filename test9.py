import streamlit as st
import requests
from bs4 import BeautifulSoup

def fetch_preview(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        def og(tag):
            meta = soup.find("meta", property=tag)
            return meta["content"] if meta else None

        return {
            "title": og("og:title") or "제목 없음",
            "description": og("og:description") or "설명 없음",
            "image": og("og:image"),
            "url": og("og:url") or url
        }
    except Exception as e:
        return {"error": str(e)}

# 예시 링크 리스트
urls = [
    "https://www.chosun.com/national/obituary-person/2025/07/30/FGLONMUDIFHHUCYE5JNTRWRACA/",
    "https://www.chosun.com/international/2025/07/30/4JMFYCHPKRDP5PXQTRDX6D5XGM/"
]

st.title("📰 AI 뉴스 미리보기 대시보드")

for url in urls:
    preview = fetch_preview(url)
    if "error" in preview:
        st.error(f"링크 에러: {preview['error']}")
        continue

    with st.container():
        cols = st.columns([1, 4])
        if preview["image"]:
            cols[0].image(preview["image"], width=100)
        with cols[1]:
            st.subheader(preview["title"])
            st.write(preview["description"])
            st.markdown(f"[🔗 기사 보기]({preview['url']})")
        st.markdown("---")