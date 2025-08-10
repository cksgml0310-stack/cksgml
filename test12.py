import streamlit as st
import pandas as pd
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="오늘의 뉴스", layout="wide")

st.title("🗞️ 오늘의 뉴스")

# Google 인증
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

with open("credentials.json", "r") as f:
    credentials = json.load(f)

creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
client = gspread.authorize(creds)

# 구글 시트 이름 입력 (기본값 'article')
SHEET_NAME = st.text_input("📎 불러올 구글 스프레드시트 이름:", "article")

try:
    sheet = client.open(SHEET_NAME).worksheet("article")  # 시트 탭 이름도 'article'
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    st.success("✅ Google Sheet에서 데이터 불러오기 성공")
except Exception as e:
    st.error(f"❌ 시트 불러오기 실패: {e}")
    st.stop()

# 오늘 날짜 표시
st.markdown(f"📅 오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
st.markdown("---")

# theme 컬럼 체크 및 버튼 UI
if "theme" not in df.columns:
    st.error("⚠️ 'theme' 컬럼이 없습니다.")
    st.stop()

themes = df["theme"].dropna().unique().tolist()
selected_theme = None

st.markdown("### 🎯 보고 싶은 주제를 선택하세요")

cols = st.columns(len(themes))
for i, theme in enumerate(themes):
    if cols[i].button(f"🟦 {theme}"):
        selected_theme = theme

if selected_theme is None and themes:
    selected_theme = themes[0]

filtered_df = df[df["theme"] == selected_theme]

# category 필터 멀티셀렉트박스
if "category" not in filtered_df.columns:
    st.error("⚠️ 'category' 컬럼이 없습니다.")
    st.stop()

all_categories = filtered_df["category"].dropna().unique().tolist()
all_categories.sort()

selected_categories = st.multiselect(
    "🔎 보고 싶은 카테고리를 선택하세요 (복수 선택 가능):",
    options=all_categories,
    default=all_categories
)

filtered_categories_df = filtered_df[filtered_df["category"].isin(selected_categories)]

# 선택된 카테고리별 뉴스 출력
for category in selected_categories:
    with st.expander(f"📘 {category}", expanded=True):
        cat_df = filtered_categories_df[filtered_categories_df["category"] == category]
        for _, row in cat_df.iterrows():
            st.markdown(f"### {row.get('title', '제목 없음')}")
            st.markdown(f"- 📰 **신문사:** {row.get('source', '출처 없음')}")
            st.markdown(f"- 📝 {row.get('summary', '요약 없음')}")
            if pd.notna(row.get("url")) and row.get("url") != "":
                st.markdown(f"[🔗 출처 보기]({row['url']})")
            st.markdown("---")
