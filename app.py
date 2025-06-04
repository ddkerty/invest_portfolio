# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# 다른 모듈에서 필요한 함수와 변수들을 가져옵니다.
from config import MAX_TICKERS, RESULT_TYPES, API_LIMIT
from api_handler import fetch_stock_data
from portfolio_analyzer import classify_portfolio

# --- 페이지 기본 설정 및 CSS 스타일 주입 ---
st.set_page_config(
    page_title="My 포트폴리오 대시보드",
    page_icon="🚀",
    layout="wide"
)

# CSS를 직접 주입하여 UI를 꾸밉니다.
css_string = """
/* Card 형태의 컨테이너 스타일 */
div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    background-color: #ffffff;
}
/* Streamlit 기본 패딩 조정으로 카드 디자인 최적화 */
.st-emotion-cache-z5fcl4 {
    padding-top: 2rem;
}
"""
st.markdown(f"<style>{css_string}</style>", unsafe_allow_html=True)


# --- 세션 상태(Session State) 초기화 ---
# 앱이 재실행되어도 데이터를 유지하기 위해 사용합니다.
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = 0 # API 호출 횟수
if 'fetched_tickers' not in st.session_state:
    st.session_state.fetched_tickers = {} # 이미 조회한 티커 정보 저장 (API 호출 최적화)


# --- ⚙️ 사이드바 (API 사용 현황) ---
st.sidebar.header("⚙️ 앱 설정 및 현황")
st.sidebar.markdown("##### API 사용량")

# 프로그레스 바로 시각적으로 표시
progress = st.session_state.api_calls / API_LIMIT
st.sidebar.progress(progress)
st.sidebar.markdown(f"**{st.session_state.api_calls} / {API_LIMIT}** 호출")
st.sidebar.info("새로운 티커를 추가할 때마다 1회씩 차감됩니다. (하루 기준)")
st.sidebar.warning("한도를 모두 소진하면 다음 날까지 새로운 종목을 추가할 수 없습니다.")


# --- 앱 제목 ---
st.title("🚀 My 포트폴리오 대시보드")
st.markdown("종목, 보유 수량, 평균 매수 단가를 입력하고 포트폴리오를 정밀 분석해보세요.")

# --- 1. 종목 추가하기 ---
st.subheader("1. 종목 추가하기", divider="gray")

# 입력 폼을 가로로 정렬
input_cols = st.columns([2, 1, 1, 0.5, 1])
with input_cols[0]:
    ticker = st.text_input("티커", placeholder="예: AAPL").upper()
with input_cols[1]:
    quantity = st.number_input("보유 수량", min_value=1, step=1)
with input_cols[2]:
    avg_price = st.number_input("내 평균 매수 단가 ($)", min_value=0.01, format="%.2f")
with input_cols[3]:
    st.write("") 
    st.write("")
    add_button = st.button("추가", use_container_width=True)

if add_button and ticker:
    # API 한도 체크 로직
    if st.session_state.api_calls >= API_LIMIT and ticker not in st.session_state.fetched_tickers:
        st.error("하루 API 사용량을 모두 소진했습니다. 내일 다시 시도해주세요.")
    else:
        is_already_in = any(item['ticker'] == ticker for item in st.session_state.portfolio)
        if is_already_in:
            st.warning(f"티커 '{ticker}'는 이미 포트폴리오에 있습니다.")
        else:
            # 새로운 티커일 경우에만 API 호출
            if ticker not in st.session_state.fetched_tickers:
                with st.spinner(f"{ticker} 정보 조회 중..."):
                    stock_info = fetch_stock_data(ticker)
                    if