# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# 다른 모듈에서 필요한 함수와 변수들을 가져옵니다.
from config import MAX_TICKERS, RESULT_TYPES, API_LIMIT
from api_handler import fetch_stock_data
from portfolio_analyzer import classify_portfolio

# --- 페이지 기본 설정 및 CSS ---
st.set_page_config(
    page_title="미국 포트폴리오 분석기",
    page_icon="📈",
    layout="wide"
)

# CSS 스타일링
css_string = """
div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    background-color: #ffffff;
}
.st-emotion-cache-z5fcl4 {
    padding-top: 2rem;
}
"""
st.markdown(f"<style>{css_string}</style>", unsafe_allow_html=True)


# --- 세션 상태 초기화 ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = 0
if 'fetched_tickers' not in st.session_state:
    st.session_state.fetched_tickers = {}

# --- 사이드바 ---
st.sidebar.header("⚙️ 앱 설정 및 현황")
st.sidebar.markdown("##### API 사용량")
progress = st.session_state.api_calls / API_LIMIT
st.sidebar.progress(progress)
st.sidebar.markdown(f"**{st.session_state.api_calls} / {API_LIMIT}** 호출")
st.sidebar.info("새로운 티커를 추가할 때마다 1회씩 차감됩니다.")


# --- 앱 제목 ---
st.title("🚀 My 포트폴리오 대시보드")
st.markdown("종목, 보유 수량, 평균 매수 단가를 입력하고 포트폴리오를 실시간으로 확인하세요.")

# --- 1. 종목 추가하기 ---
st.subheader("1. 종목 추가하기", divider="gray")

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
    if st.session_state.api_calls >= API_LIMIT and ticker not in st.session_state.fetched_tickers:
        st.error("하루 API 사용량을 모두 소진했습니다.")
    else:
        is_already_in = any(item['ticker'] == ticker for item in st.session_state.portfolio)
        if is_already_in:
            st.warning(f"티커 '{ticker}'는 이미 포트폴리오에 있습니다.")
        else:
            if ticker not in st.session_state.fetched_tickers:
                with st.spinner(f"{ticker} 정보 조회 중..."):
                    stock_info = fetch_stock_data(ticker)
                    if stock_info:
                        st.session_state.fetched_tickers[ticker] = stock_info
                        st.session_state.api_calls += 1
                    else:
                        st.error(f"'{ticker}' 정보를 가져오는 데 실패했습니다.")
            
            if ticker in st.session_state.fetched_tickers:
                new_stock = {'ticker': ticker, 'quantity': quantity, 'avg_price': avg_price}
                st.session_state.portfolio.append(new_stock)
                st.rerun()

# --- 2. 실시간 포트폴리오 현황 ---
if st.session_state.portfolio:
    st.subheader("📊 실시간 포트폴리오 현황", divider="gray")

    # --- 실시간 데이터 계산 및 표시 ---
    display_data = []
    total_current_value = 0
    total_purchase_cost = 0

    for item in st.session_state.portfolio:
        ticker = item['ticker']
        if ticker in st.session_state.fetched_tickers:
            stock = st.session_state.fetched_tickers[ticker]
            quantity = item['quantity']
            avg_price = item['avg_price']
            current_price = stock.get('price', 0)
            
            purchase_cost = avg_price * quantity
            current_value = current_price * quantity
            profit_loss = current_value - purchase_cost
            return_rate = (profit_loss / purchase_cost) * 100 if purchase_cost > 0 else 0

            total_current_value += current_value
            total_purchase_cost += purchase_cost

            display_data.append({
                "티커": stock.get('symbol'), "보유 수량": quantity,
                "매수 평균가": f"${avg_price:,.2f}", "현재가": f"${current_price:,.2f}",
                "평가액": f"${current_value:,.2f}", "평가 손익": f"${profit_loss:,.2f}",
                "수익률(%)": f"{return_rate:.2f}%"
            })
    
    # --- 실시간 요약 메트릭 ---
    total_profit_loss = total_current_value - total_purchase_cost
    total_return_rate = (total_profit_loss / total_purchase_cost) * 100 if total_purchase_cost > 0 else 0

    summary_cols = st.columns(2)
    with summary_cols[0]:
        st.metric(label="현재 총 평가액", value=f"${total_current_value:,.2f}")
    with summary_cols[1]:
        st.metric(label="총 평가 손익", value=f"${total_profit_loss:,.2f}", delta=f"{total_return_rate:.2f}%")

    # --- 실시간 상세 테이블 ---
    df_detail = pd.DataFrame(display_data)
    st.dataframe(df_detail, use_container_width=True, hide_index=True)

    if st.button("목록 초기화", type="secondary"):
        st.session_state.portfolio = []
        st.rerun()

    st.markdown("---")

    # --- 3. 포트폴리오 심층 분석 ---
    if st.button("🔬 포트폴리오 심층 분석 실행", use_container_width=True, type="primary"):
        with st.spinner("포트폴리오를 심층 분석 중입니다..."):
            
            final_portfolio_data = []
            for item in st.session_state.portfolio:
                if item['ticker'] in st.session_state.fetched_tickers:
                    final_portfolio_data.append({
                        'stock': st.session_state.fetched_tickers[item['ticker']],
                        'quantity': item['quantity'],
                        'avg_price': item['avg_price']
                    })
            
            final_type, sector_values, _ = classify_portfolio(final_portfolio_data)

            # --- 심층 분석 결과 출력 ---
            st.subheader("🧬 심층 분석 결과", divider="rainbow")
            
            analysis_cols = st.columns([1,2])
            with analysis_cols[0]:
                st.markdown("##### 포트폴리오 성향")
                result_info = RESULT_TYPES[final_type]
                st.header(result_info['name'])
                st.write(result_info['desc'])

            with analysis_cols[1]:
                st.markdown("##### 섹터별 자산 분포")
                if sector_values:
                    fig = px.pie(names=list(sector_values.keys()), values=list(sector_values.values()), hole=0.5)
                    fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=False, textfont_size=14)
                    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("종목을 추가하여 실시간 포트폴리오 대시보드를 구성해보세요.")
    st.info("티커는 최대 15개까지 추가할 수 있습니다. API 호출 제한에 유의하세요.")