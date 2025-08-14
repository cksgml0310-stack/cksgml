import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import google.generativeai as genai
import re

# --- 페이지 설정 ---
st.set_page_config(layout="wide")

# 제미나이 API 키 설정
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
        # 연도 정보가 없는 날짜 포맷에 2025년을 직접 추가하여 파싱
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

# --- 사이드바 필터 영역 ---
with st.sidebar:
    st.title("⚙️ 필터 설정")
    all_themes = sorted(df["theme"].dropna().unique())
    selected_themes = st.multiselect(
        "🏷️ 테마 선택", 
        all_themes, 
        default=all_themes
    )

    valid_dates = df["date"].dropna()
    start_date = st.date_input(
        "🗓️ 시작일",
        value=valid_dates.min().date() if not valid_dates.empty else datetime.now().date()
    )
    end_date = st.date_input(
        "🗓️ 종료일",
        value=valid_dates.max().date() if not valid_dates.empty else datetime.now().date()
    )

    search_query = st.text_input(
        "🔍 키워드 검색", 
        placeholder="제목 또는 요약에 포함된 키워드를 입력하세요."
    )
    
    st.markdown("---")
    st.subheader("🤖 AI 분석 설정")
    num_summary = st.number_input(
        "요약 항목 개수", 
        min_value=1, 
        max_value=10, 
        value=5, 
        step=1,
        help="AI가 요약해 줄 트렌드 항목의 최대 개수를 설정합니다."
    )

# 세션 상태에 현재 필터 상태 저장
current_filters = {
    "themes": selected_themes,
    "start_date": start_date,
    "end_date": end_date,
    "search_query": search_query,
    "num_summary": num_summary
}

if 'last_filters' not in st.session_state:
    st.session_state.last_filters = current_filters
    st.session_state.filters_changed = True
    st.session_state.search_history = {} # 검색 기록 초기화
else:
    if st.session_state.last_filters != current_filters:
        st.session_state.filters_changed = True
        st.session_state.last_filters = current_filters
    else:
        st.session_state.filters_changed = False

# --- 메인 화면 ---
st.title("📰 SK networks 뉴스")
st.markdown("---")

# --- 필터링 로직 ---
filtered_df = df.copy()
if selected_themes:
    filtered_df = filtered_df[filtered_df["theme"].isin(selected_themes)]

if start_date and end_date:
    filtered_df = filtered_df[
        (filtered_df["date"].dt.date >= start_date) & 
        (filtered_df["date"].dt.date <= end_date)
    ]

if search_query:
    # 검색 기록 업데이트
    if 'search_history' not in st.session_state:
        st.session_state.search_history = {}
    if search_query in st.session_state.search_history:
        st.session_state.search_history[search_query] += 1
    else:
        st.session_state.search_history[search_query] = 1

    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False) |
        filtered_df.get("summary", pd.Series(dtype='object')).str.contains(search_query, case=False, na=False)
    ]

# --- 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["📊 뉴스 검색 결과", "🤖 통합 인사이트 & 보고서", "📈 검색 통계"])

with tab1:
    if not filtered_df.empty:
        categories = filtered_df["category"].dropna().unique()
        for category in categories:
            with st.expander(f"📚 {category} ({(filtered_df['category'] == category).sum()}건)", expanded=True):
                cat_df = filtered_df[filtered_df["category"] == category]
                for _, row in cat_df.iterrows():
                    st.markdown(f"### 💡 {row['title']}")
                    st.markdown(f"- 🏢 **{row['source']}** ({row['date'].strftime('%Y-%m-%d')})")
                    st.markdown(f"- 📌 {row.get('summary', '요약 없음')}")
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
        topic_value = ""
        if search_query:
            topic_value = f'"{search_query}"'
        elif len(selected_themes) == 1:
            topic_value = selected_themes[0]
        
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
                report_col, download_col = st.columns([1, 0.2])
                with report_col:
                    st.subheader("📄 생성된 보고서")
                    st.markdown(f'<div class="report-box">{st.session_state.generated_report}</div>', unsafe_allow_html=True)
                
                with download_col:
                    report_bytes = st.session_state.generated_report.encode('utf-8')
                    st.download_button(
                        label="📄 다운로드",
                        data=report_bytes,
                        file_name=f"SK_networks_뉴스_보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )

with tab3:
    st.subheader("📈 키워드 검색 선호도")
    if 'search_history' in st.session_state and st.session_state.search_history:
        search_counts = pd.DataFrame(st.session_state.search_history.items(), columns=['키워드', '검색 횟수'])
        search_counts = search_counts.sort_values(by='검색 횟수', ascending=False)
        
        st.write("가장 많이 검색된 키워드:")
        st.dataframe(search_counts, hide_index=True, use_container_width=True)
        
        # 시각화
        st.bar_chart(search_counts.set_index('키워드'))
    else:
        st.info("아직 검색된 키워드가 없습니다. 키워드 검색을 실행하여 통계를 확인해 보세요.")