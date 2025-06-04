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
    page_title="미국국 포트폴리오 대시보드",
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
                    if stock_info:
                        st.session_state.fetched_tickers[ticker] = stock_info
                        st.session_state.api_calls += 1
                    else:
                        st.error(f"'{ticker}' 정보를 가져오는 데 실패했습니다.")
            
            # API 호출에 성공했거나, 이미 조회한 티커인 경우 포트폴리오에 추가
            if ticker in st.session_state.fetched_tickers:
                new_stock = {'ticker': ticker, 'quantity': quantity, 'avg_price': avg_price}
                st.session_state.portfolio.append(new_stock)
                st.rerun() # 추가 후 화면 새로고침

# --- 현재 포트폴리오 목록 표시 ---
if st.session_state.portfolio:
    st.markdown("##### 현재 포트폴리오 목록")
    df_portfolio = pd.DataFrame(st.session_state.portfolio)
    st.dataframe(df_portfolio, use_container_width=True, hide_index=True)
    if st.button("목록 초기화", type="secondary"):
        # 초기화 시 API 호출 횟수는 유지
        st.session_state.portfolio = []
        st.rerun()

st.markdown("---")

# --- 2. 분석 실행 버튼 ---
if st.session_state.portfolio:
    if st.button("📈 포트폴리오 정밀 분석 실행", use_container_width=True, type="primary"):
        with st.spinner("최신 시세를 반영하여 포트폴리오를 분석 중입니다..."):
            
            # 분석을 위한 최종 데이터 구조화
            final_portfolio_data = []
            for item in st.session_state.portfolio:
                if item['ticker'] in st.session_state.fetched_tickers:
                    stock_info = st.session_state.fetched_tickers[item['ticker']]
                    final_portfolio_data.append({
                        'stock': stock_info,
                        'quantity': item['quantity'],
                        'avg_price': item['avg_price']
                    })

            if not final_portfolio_data:
                st.error("분석할 유효한 종목이 없습니다.")
            else:
                final_type, sector_values, total_value = classify_portfolio(final_portfolio_data)
                
                # --- 3. 분석 결과 대시보드 ---
                st.subheader("📊 분석 결과 대시보드", divider="rainbow")
                
                # 결과 요약
                summary_cols = st.columns(3)
                with summary_cols[0]:
                    st.markdown("##### 포트폴리오 성향")
                    result_info = RESULT_TYPES[final_type]
                    st.header(result_info['name'])
                    st.write(result_info['desc'])
                with summary_cols[1]:
                    st.markdown("##### 포트폴리오 가치")
                    st.metric(label="현재 총 평가액", value=f"${total_value:,.2f}")
                    total_purchase_cost = sum(item['avg_price'] * item['quantity'] for item in final_portfolio_data)
                    total_profit_loss = total_value - total_purchase_cost
                    total_return_rate = (total_profit_loss / total_purchase_cost) * 100 if total_purchase_cost > 0 else 0
                    st.metric(label="총 평가 손익", value=f"${total_profit_loss:,.2f}", delta=f"{total_return_rate:.2f}%")
                
                with summary_cols[2]:
                    st.markdown("##### 자산 분포 (Top 3 섹터)")
                    sorted_sectors = sorted(sector_values.items(), key=lambda x: x[1], reverse=True)
                    for i in range(min(3, len(sorted_sectors))):
                        sector, value = sorted_sectors[i]
                        st.text(f"{i+1}. {sector}: ${value:,.0f}")

                st.markdown("---")
                
                # 상세 현황 및 섹터 분포
                detail_cols = st.columns([3, 2])
                with detail_cols[0]:
                    st.markdown("##### 상세 보유 현황 (수익률 포함)")
                    display_data = []
                    for item in final_portfolio_data:
                        stock = item['stock']
                        quantity = item['quantity']
                        avg_price = item['avg_price']
                        current_price = stock.get('price', 0)
                        
                        purchase_cost = avg_price * quantity
                        current_value = current_price * quantity
                        profit_loss = current_value - purchase_cost
                        return_rate = (profit_loss / purchase_cost) * 100 if purchase_cost > 0 else 0

                        display_data.append({
                            "티커": stock.get('symbol'), "보유 수량": quantity,
                            "매수 평균가": f"${avg_price:,.2f}", "현재가": f"${current_price:,.2f}",
                            "평가 손익": f"${profit_loss:,.2f}", "수익률(%)": f"{return_rate:.2f}%"
                        })
                    df_detail = pd.DataFrame(display_data)
                    st.dataframe(df_detail, use_container_width=True, hide_index=True)

                with detail_cols[1]:
                    st.markdown("##### 섹터별 자산 분포")
                    if sector_values:
                        fig = px.pie(names=list(sector_values.keys()), values=list(sector_values.values()), hole=0.5)
                        fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=False, textfont_size=14)
                        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)

# 포트폴리오에 종목이 하나도 없을 때 안내 메시지 표시
else:
    st.info("좌측 상단의 사이드바에서 API 사용 현황을 확인하고, 종목을 추가하여 분석을 시작하세요.")
    st.info("추가 버튼을 누르면 내 포트폴리오에 종목이 추가됩니다. 최대 15개 티커까지 지원합니다.")