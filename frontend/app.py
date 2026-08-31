import os

import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="stock_insight", layout="wide")
st.title("stock_insight")
st.caption("종목명을 입력하면 근거 있는 분석을 보여줍니다.")

stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
if stock_name:
    st.info(f"'{stock_name}' 분석은 backend 연동 후 표시됩니다. ({BACKEND_URL})")
