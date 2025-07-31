import streamlit as st

st.title("👋 나의 첫 Streamlit 앱")
st.write("안녕하세요! Streamlit에 오신 걸 환영합니다.")

name = st.text_input("이름을 입력하세요")
if name:
    st.success(f"{name}님, 반가워요!")