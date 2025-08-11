import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import google.generativeai as genai
import pdfkit
import io
import base64
import re

# --- 페이지 설정 ---
st.set_page_config(layout="wide")

# 제미나이 API 키 설정
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except KeyError:
    st.error("API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인해 주세요.")
    st.stop()
except Exception as e:
    st.error(f"제미나이 설정 중 오류 발생: {e}")
    st.stop()

# --- CSS 스타일 적용 (전체 너비 강제 적용) ---
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
        
        /* 요약 내용의 세로 간격 일정하게 조정 */
        .gemini-summary ol, .gemini-summary ul {
            padding-left: 20px;
        }
        .gemini-summary li {
            font-size: 1.1em;
            line-height: 1.8;
            margin-bottom: 10px;
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

def clear_analysis_result():
    if 'analysis_result' in st.session_state:
        del st.session_state.analysis_result
    if 'analysis_title' in st.session_state:
        del st.session_state.analysis_title

# --- PDF 생성 함수 (분석 내용만) ---
def create_analysis_pdf(analysis_result, analysis_title):
    try:
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        
        # HTML 리스트로 변환하는 로직을 PDF 생성 함수에 포함
        summary_lines = analysis_result.split('\n')
        list_html = '<ol>'
        for line in summary_lines:
            if line.strip() and re.match(r'^\d+\.', line.strip()):
                list_html += f'<li>{line.strip()[2:].strip()}</li>'
        list_html += '</ol>'

        # HTML 내용에 요약 결과와 제목, CSS를 직접 포함
        pdf_html_content = f"""
        <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ 
                        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Nanum Gothic', sans-serif;
                        line-height: 1.8;
                    }}
                    h1 {{ color: #004488; }}
                    .summary-box {{ border: 1px solid #e6e6e6; padding: 15px; border-radius: 5px; background-color: #f9f9f9; }}
                    h3 {{ color: #555555; }}
                    ol {{ padding-left: 20px; }}
                    li {{ font-size: 1.1em; line-height: 1.8; margin-bottom: 10px; }}
                </style>
            </head>
            <body>
                <h1>{analysis_title}</h1>
                <hr>
                <h3>트렌드 요약</h3>
                <div class="summary-box">
                    {list_html}
                </div>
            </body>
        </html>
        """
        
        pdf_bytes = pdfkit.from_string(
            pdf_html_content, 
            False, 
            configuration=config,
            options={'enable-local-file-access': None}
        )
        return pdf_bytes
    except Exception as e:
        st.error(f"PDF 생성 중 오류 발생: {e}")
        return None

# --- 제목과 버튼 영역 ---
title_col, button_col = st.columns([1, 0.4])
with title_col:
    st.title("📰 SK networks 뉴스")

st.markdown("---")

# --- 필터 영역 ---
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    all_themes = sorted(df["theme"].dropna().unique())
    selected_themes = st.multiselect(
        "🏷️ 테마 선택", 
        all_themes, 
        default=all_themes,
        on_change=clear_analysis_result
    )

with filter_col2:
    valid_dates = df["date"].dropna()
    date_start_col, date_end_col = st.columns(2)
    with date_start_col:
        start_date = st.date_input(
            "🗓️ 시작일",
            value=valid_dates.max().date() if not valid_dates.empty else datetime.now().date(),
            on_change=clear_analysis_result
        )
    with date_end_col:
        end_date = st.date_input(
            "🗓️ 종료일",
            value=valid_dates.max().date() if not valid_dates.empty else datetime.now().date(),
            on_change=clear_analysis_result
        )

search_query = st.text_input(
    "🔍 키워드 검색", 
    placeholder="제목 또는 요약에 포함된 키워드를 입력하세요.",
    on_change=clear_analysis_result
)

# --- 필터링 로직 ---
filtered_df = df.copy()
filtered_by_date = False
filtered_by_keyword = False

if selected_themes:
    filtered_df = filtered_df[filtered_df["theme"].isin(selected_themes)]

if start_date and end_date:
    filtered_df = filtered_df[
        (filtered_df["date"].dt.date >= start_date) & 
        (filtered_df["date"].dt.date <= end_date)
    ]
    if len(filtered_df) == 0:
        filtered_by_date = True

if search_query:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False) |
        filtered_df.get("summary", pd.Series(dtype='object')).str.contains(search_query, case=False, na=False)
    ]
    if len(filtered_df) == 0:
        filtered_by_keyword = True

# --- 제미나이 분석 섹션 ---
st.markdown("---")

# 동적 제목 생성 로직
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

if filtered_df.empty:
    st.info("뉴스 분석을 위해 먼저 필터를 설정해 주세요.")
else:
    articles_text = ""
    for _, row in filtered_df.iterrows():
        articles_text += f"제목: {row['title']}\n요약: {row.get('summary', '요약 없음')}\n\n"
    
    analysis_prompt = f"""
    아래에 제공된 뉴스 기사들을 분석하여, 1. 2. 3. 4. 5.와 같이 최대 5개의 번호로 핵심 트렌드와 사견을 요약해 줘. 각 항목은 한 문장으로 작성하고, 줄바꿈으로 구분해. 특별한 서식(볼드체, 따옴표 등)은 사용하지 마.
    뉴스 기사:
    {articles_text}
    """
    
    analyze_btn_col, pdf_btn_col = st.columns([0.25, 0.75])
    
    with analyze_btn_col:
        if st.button("✨ 트렌드 분석 시작"):
            with st.spinner("제미나이가 뉴스 트렌드를 분석하고 있습니다..."):
                try:
                    response = gemini_model.generate_content(analysis_prompt)
                    st.session_state.analysis_title = f"📰 {date_prefix} {topic_value} 트렌드"
                    st.session_state.analysis_result = response.text
                except Exception as e:
                    st.error(f"제미나이 API 호출 중 오류 발생: {e}")

    if 'analysis_result' in st.session_state and st.session_state.analysis_result:
        with pdf_btn_col:
            pdf_bytes = create_analysis_pdf(st.session_state.analysis_result, st.session_state.analysis_title)
            if pdf_bytes:
                st.download_button(
                    label="⬇️ PDF 출력",
                    data=pdf_bytes,
                    file_name=f"SK_networks_뉴스_분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/octet-stream"
                )
    
    if 'analysis_result' in st.session_state:
        st.subheader(st.session_state.analysis_title)
        
        summary_lines = st.session_state.analysis_result.split('\n')
        list_html = '<ol class="gemini-summary">'
        for line in summary_lines:
            if line.strip():
                if re.match(r'^\d+\.', line.strip()):
                    list_html += f'<li>{line.strip()[2:].strip()}</li>'
                else:
                    list_html += f'<li>{line.strip()}</li>'
        list_html += '</ol>'
        st.markdown(list_html, unsafe_allow_html=True)

st.markdown("---")

# --- 뉴스 출력 ---
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
                    with st.expander("🖼️ 미리보기", expanded=True):
                        components.html(
                            f'<iframe src="{row["url"]}" width="100%" height="600px"></iframe>',
                            height=600,
                            scrolling=False
                        )
                        st.info("미리보기가 보이지 않는다면, 해당 웹사이트에서 미리보기 기능을 지원하지 않는 것일 수 있습니다.")
                st.markdown("---")
else:
    st.markdown("### 😥 해당 뉴스 없음")
    if filtered_by_date:
        st.markdown("날짜를 다시 설정하세요")
    if filtered_by_keyword:
        st.markdown("키워드를 다시 설정하세요")