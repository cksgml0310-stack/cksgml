import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import google.generativeai as genai
import re
import os

# --- 페이지 설정 ---
st.set_page_config(layout="wide")

# 제미나이 API 키 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Google API 키가 Streamlit Secrets에 설정되지 않았습니다.")
    st.stop()

genai.configure(api_key=st.secrets.GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

# --- CSS 스타일 적용 ---
st.markdown("""
    <style>
        body {
            background-color: #f7f7f7;
            font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Nanum Gothic', sans-serif;
        }
        .stButton>button {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e6e6e6;
            border-radius: 5px;
        }
        .stMultiSelect div[data-baseweb="select"] {
            border-color: #e6e6e6;
        }
        .stTextInput div[data-baseweb="input"] {
            border-color: #e6e6e6;
        }
        
        .main .block-container {
            width: 100% !important;
            max-width: none !important;
        }
        
        iframe {
            width: 100% !important;
            height: 600px !important;
            border: 1px solid #e6e6e6;
            border-radius: 5px;
            overflow: hidden !important;
        }
        
        .gemini-summary ol, .gemini-summary ul {
            padding-left: 20px;
        }
        .gemini-summary li {
            font-size: 1.1em;
            line-height: 1.8;
            margin-bottom: 10px;
        }
        
        .report-box {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
        }
        
        /* 사이드바 너비 조정 */
        section[data-testid="stSidebar"] {
            width: 350px !important; 
        }

        /* 테마 선택 박스 스타일 */
        div.st-emotion-cache-1j4kn0p {
            border: 1px solid #e6e6e6;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
            background-color: #ffffff;
        }

        /* AI 추천 기사 박스 스타일 */
        .ai-recommendation-box {
            background-color: #e6f7ff;
            border: 2px solid #0073e6;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .ai-recommendation-box h4 {
            color: #004085;
        }
    </style>
""", unsafe_allow_html=True)

# --- 구글 스프레드시트 CSV URL ---
CSV_URL = "https://docs.google.com/spreadsheets/d/14I9HkPiBhKs6nXLt6kEBalQHeasrwINWshFDghTHbZE/gviz/tq?tqx=out:csv&sheet=Sheet1"

# --- 데이터 불러오기 ---
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    required_cols = {"date", "category", "theme", "title", "source"}
    if not required_cols.issubset(df.columns):
        st.error(f"필수 컬럼 누락: {required_cols - set(df.columns)}")
        return pd.DataFrame()
    try:
        df["date"] = pd.to_datetime(df["date"].str.strip('"') + " 2025", format="%a, %d %b %Y")
    except Exception as e:
        st.error("날짜 포맷 오류 발생. 스프레드시트의 날짜 형식을 확인하세요.")
        st.exception(e)
        return pd.DataFrame()
    return df

df = load_data()

if df.empty:
    st.stop()

df['category'] = df['category'].fillna(df['theme'])

# 세션 상태 초기화
def clear_analysis_result():
    for key in ['analysis_result', 'analysis_title', 'generated_report']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.filters_changed = True

# --- 보고서 생성 함수 ---
def generate_report(filtered_df, analysis_result):
    articles_text = ""
    for _, row in filtered_df.iterrows():
        articles_text += f"제목: {row['title']}\n출처: {row['source']} ({row['date'].strftime('%Y-%m-%d')})\n요약: {row.get('summary', '요약 없음')}\nURL: {row.get('url', '없음')}\n\n"

    report_prompt = f"""
    [트렌드 분석 결과]
    {analysis_result}
    
    [필터링된 뉴스 기사 목록]
    {articles_text}
    
    위 트렌드 분석 결과와 뉴스 기사 목록을 바탕으로, 다음 내용을 포함하는 보고서를 500자 이내로 작성해 주세요.
    명확한 제목과 함께 아래 항목들을 포함하여 하나의 자연스러운 보고서 형태로 작성해 주세요.
    1. 주요 뉴스 내용 요약
    2. 나타나는 주요 트렌드 및 시사점
    3. 전체적인 의견
    """
    try:
        response = gemini_model.generate_content(report_prompt)
        st.session_state.generated_report = response.text
        st.success("보고서가 생성되었습니다.")
    except Exception as e:
        st.error(f"보고서 생성 중 오류 발생: {e}")

# --- AI 추천 기사 생성 함수 ---
def generate_recommendations(filtered_df):
    articles_text = ""
    for _, row in filtered_df.iterrows():
        articles_text += f"제목: {row['title']}\n요약: {row.get('summary', '요약 없음')}\n"
    
    recommendation_prompt = f"""
    아래 뉴스 기사 목록을 분석하여, 가장 중요하거나 영향력 있는 기사 1~2개를 선정하고 그 이유를 간결하게 설명해 줘. 
    선정된 기사 제목과 선정이유를 명확히 구분하여 작성해. 
    뉴스 기사:
    {articles_text}
    """
    try:
        response = gemini_model.generate_content(recommendation_prompt)
        return response.text
    except Exception as e:
        return f"AI 추천 기사 생성 중 오류 발생: {e}"

# --- 세션 상태 초기화 및 관리 ---
if 'last_filters' not in st.session_state:
    st.session_state.last_filters = {}
    st.session_state.filters_changed = True
if 'search_history' not in st.session_state:
    st.session_state.search_history = {}
if 'likes' not in st.session_state:
    st.session_state.likes = {}
if 'dislikes' not in st.session_state:
    st.session_state.dislikes = {}
if 'selected_themes' not in st.session_state:
    st.session_state.selected_themes = list(sorted(df["theme"].dropna().unique()))

# --- 사이드바 필터 영역 ---
with st.sidebar:
    st.title("⚙️ 뉴스 필터")
    
    all_themes = sorted(df["theme"].dropna().unique())
    
    st.subheader("🏷️ 테마 선택")
    theme_cols = st.columns(3)
    if theme_cols[0].button("전체 선택", use_container_width=True):
        st.session_state.selected_themes = all_themes
    if theme_cols[2].button("전체 해제", use_container_width=True):
        st.session_state.selected_themes = []

    selected_themes_box = []
    for theme in all_themes:
        if st.checkbox(theme, value=theme in st.session_state.selected_themes, key=f"theme_{theme}"):
            selected_themes_box.append(theme)
    st.session_state.selected_themes = selected_themes_box

    st.markdown("---")
    
    valid_dates = df["date"].dropna()
    latest_date = valid_dates.max().date() if not valid_dates.empty else datetime.now().date()
    
    start_date = st.date_input(
        "🗓️ 시작일",
        value=latest_date
    )
    end_date = st.date_input(
        "🗓️ 종료일",
        value=latest_date
    )

    search_query = st.text_input(
        "🔍 키워드 검색", 
        placeholder="검색할 키워드를 입력하세요."
    )

    st.markdown("---")
    st.subheader("❓ 제미나이에게 질문하기")
    gemini_query = st.text_input(
        "궁금한 점을 물어보세요.", 
        placeholder="예: SK네트웍스의 최근 사업 방향에 대해 알려줘."
    )
    if st.button("질문하기", use_container_width=True):
        if gemini_query:
            with st.spinner("답변을 생성하는 중..."):
                try:
                    response = gemini_model.generate_content(gemini_query)
                    st.session_state.gemini_response = response.text
                except Exception as e:
                    st.session_state.gemini_response = f"질문 처리 중 오류 발생: {e}"
        else:
            st.session_state.gemini_response = "질문을 입력해 주세요."
    if 'gemini_response' in st.session_state:
        st.info(st.session_state.gemini_response)

# --- 필터링 로직 ---
current_filters = {
    "themes": st.session_state.selected_themes,
    "start_date": start_date,
    "end_date": end_date,
    "search_query": search_query
}

if st.session_state.last_filters != current_filters:
    st.session_state.filters_changed = True
    st.session_state.last_filters = current_filters
    # 필터 변경 시 AI 추천 기사 결과도 초기화
    if 'recommendations_result' in st.session_state:
        del st.session_state.recommendations_result
else:
    st.session_state.filters_changed = False

filtered_df = df.copy()
if st.session_state.selected_themes:
    filtered_df = filtered_df[filtered_df["theme"].isin(st.session_state.selected_themes)]

if start_date and end_date:
    filtered_df = filtered_df[
        (filtered_df["date"].dt.date >= start_date) & 
        (filtered_df["date"].dt.date <= end_date)
    ]

if search_query:
    if search_query in st.session_state.search_history:
        st.session_state.search_history[search_query] += 1
    else:
        st.session_state.search_history[search_query] = 1

    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False) |
        filtered_df.get("summary", pd.Series(dtype='object')).str.contains(search_query, case=False, na=False)
    ]

# --- 메인 화면 ---
st.title("📰 SK networks 뉴스")
st.markdown("---")

# --- 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["📊 뉴스 검색", "🤖 통합 인사이트 & 보고서", "📈 검색 통계"])

with tab1:
    if not filtered_df.empty:
        categories = filtered_df["category"].dropna().unique()
        for category in categories:
            with st.expander(f"📚 {category} ({(filtered_df['category'] == category).sum()}건)", expanded=True):
                cat_df = filtered_df[filtered_df["category"] == category]
                for idx, row in cat_df.iterrows():
                    st.markdown(f"### 💡 {row['title']}")
                    st.markdown(f"- 🏢 **{row['source']}** ({row['date'].strftime('%Y-%m-%d')})")
                    st.markdown(f"- 📌 {row.get('summary', '요약 없음')}")

                    # 좋아요/싫어요 버튼 추가
                    like_col, dislike_col, space_col = st.columns([0.1, 0.1, 0.8])
                    with like_col:
                        if st.button("👍", key=f"like_{idx}"):
                            st.session_state.likes[idx] = st.session_state.likes.get(idx, 0) + 1
                    with dislike_col:
                        if st.button("👎", key=f"dislike_{idx}"):
                            st.session_state.dislikes[idx] = st.session_state.dislikes.get(idx, 0) + 1
                    
                    st.write(f"👍 {st.session_state.likes.get(idx, 0)} | 👎 {st.session_state.dislikes.get(idx, 0)}")

                    if pd.notna(row.get("url")) and row["url"] != "":
                        st.markdown(f"[📖 본문 보기]({row['url']})")
                        with st.expander("🖼️ 미리보기", expanded=False):
                            components.html(
                                f'<iframe src="{row["url"]}" width="100%" height="600px"></iframe>',
                                height=600,
                                scrolling=False
                            )
                            st.info("미리보기가 보이지 않는다면, 해당 웹사이트에서 미리보기 기능을 지원하지 않는 것일 수 있습니다.")
                    st.markdown("---")
    else:
        st.markdown("### 😥 해당 뉴스 없음")
        st.info("날짜, 테마 또는 키워드 필터를 다시 설정해 보세요.")

with tab2:
    if filtered_df.empty:
        st.info("뉴스 분석을 위해 먼저 필터를 설정해 주세요.")
    else:
        # AI 추천 기사 섹션
        st.subheader("⭐ AI 추천 기사")
        if 'recommendations_result' not in st.session_state or st.session_state.get('filters_changed', False):
            with st.spinner("AI가 추천 기사를 선별하고 있습니다..."):
                st.session_state.recommendations_result = generate_recommendations(filtered_df)
        
        st.markdown(f'<div class="ai-recommendation-box">{st.session_state.recommendations_result}</div>', unsafe_allow_html=True)
        st.markdown("---")

        st.subheader("🤖 AI 분석 설정")
        summary_options = {
            "간략하게": 3,
            "보통": 5,
            "상세하게": 7
        }
        summary_level = st.radio(
            "요약 정도 선택", 
            list(summary_options.keys()), 
            index=1,
            help="AI가 요약해 줄 트렌드 항목의 길이를 설정합니다."
        )
        num_summary = summary_options[summary_level]
        
        st.markdown("---")

        topic_value = ""
        if search_query:
            topic_value = f'"{search_query}"'
        elif len(st.session_state.selected_themes) == 1:
            topic_value = st.session_state.selected_themes[0]
        
        date_prefix = ""
        if not valid_dates.empty and valid_dates.max().date() == start_date and valid_dates.max().date() == end_date:
            date_prefix = "오늘의"
        else:
            date_prefix = f"{start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}의"
        
        if st.session_state.get('filters_changed', True) or 'analysis_result' not in st.session_state:
            st.warning("필터가 변경되었습니다. 새로운 트렌드 분석을 시작하려면 아래 버튼을 클릭하세요.")
            if st.button("✨ 트렌드 분석 시작", key="start_analysis"):
                with st.spinner("제미나이가 뉴스 트렌드를 분석하고 있습니다..."):
                    articles_text = ""
                    for _, row in filtered_df.iterrows():
                        articles_text += f"제목: {row['title']}\n요약: {row.get('summary', '요약 없음')}\n\n"
                    
                    analysis_prompt = f"""
                    아래에 제공된 뉴스 기사들을 분석하여, 1. 2. 3. ...와 같이 최대 {num_summary}개의 번호로 핵심 트렌드와 사견을 요약해 줘. 각 항목은 한 문장으로 작성하고, 줄바꿈으로 구분해. 특별한 서식(볼드체, 따옴표 등)은 사용하지 마.
                    뉴스 기사:
                    {articles_text}
                    """
                    try:
                        response = gemini_model.generate_content(analysis_prompt)
                        st.session_state.analysis_title = f"📰 {date_prefix} {topic_value} 트렌드"
                        st.session_state.analysis_result = response.text
                        st.session_state.filters_changed = False
                    except Exception as e:
                        st.error(f"제미나이 API 호출 중 오류 발생: {e}")

        if 'analysis_result' in st.session_state and not st.session_state.get('filters_changed', False):
            st.subheader(st.session_state.analysis_title)
            
            summary_lines = st.session_state.analysis_result.split('\n')
            list_html = '<ol class="gemini-summary">'
            for line in summary_lines:
                if line.strip():
                    clean_line = re.sub(r'^\d+\.\s*', '', line.strip())
                    list_html += f'<li>{clean_line}</li>'
            list_html += '</ol>'
            st.markdown(list_html, unsafe_allow_html=True)
            
            st.markdown("---")
            if st.button("📝 보고서 만들기", key="create_report"):
                with st.spinner("보고서를 생성하고 있습니다..."):
                    analysis_result_for_report = st.session_state.get('analysis_result', None)
                    if analysis_result_for_report:
                        generate_report(filtered_df, analysis_result_for_report)
                    else:
                        st.warning("먼저 '트렌드 분석'을 실행하여 분석 결과를 생성해 주세요.")
            
            if 'generated_report' in st.session_state:
                st.subheader("📄 생성된 보고서")
                st.markdown(f'<div class="report-box">{st.session_state.generated_report}</div>', unsafe_allow_html=True)
                
                report_text = f"통합 인사이트\n\n{st.session_state.analysis_result}\n\n---\n\n생성된 보고서\n\n{st.session_state.generated_report}"
                report_bytes = report_text.encode('utf-8')

                st.download_button(
                    label="📥 보고서 다운로드 (TXT)",
                    data=report_bytes,
                    file_name=f"SK_networks_뉴스_보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                st.success("TXT 파일 생성이 완료되었습니다.")

with tab3:
    st.subheader("📈 키워드 검색 선호도")
    if 'search_history' in st.session_state and st.session_state.search_history:
        search_counts = pd.DataFrame(st.session_state.search_history.items(), columns=['키워드', '검색 횟수'])
        search_counts = search_counts.sort_values(by='검색 횟수', ascending=False)
        
        st.write("가장 많이 검색된 키워드:")
        st.dataframe(search_counts, hide_index=True, use_container_width=True)
        
        st.bar_chart(search_counts.set_index('키워드'))
    else:
        st.info("아직 검색된 키워드가 없습니다. 키워드 검색을 실행하여 통계를 확인해 보세요.")

    st.markdown("---")
    st.subheader("❤️ 좋아요 순위 (Top 5)")
    if st.session_state.likes:
        liked_news = pd.DataFrame(st.session_state.likes.items(), columns=['index', '좋아요 수'])
        liked_news = liked_news.sort_values(by='좋아요 수', ascending=False).head(5)
        
        liked_titles = []
        for idx in liked_news['index']:
            liked_titles.append(df.loc[idx]['title'])
        
        liked_news['제목'] = liked_titles
        st.dataframe(liked_news[['제목', '좋아요 수']], hide_index=True, use_container_width=True)
    else:
        st.info("아직 좋아요를 받은 뉴스가 없습니다. 좋아요 버튼을 눌러보세요.")