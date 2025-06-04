# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# 로컬 모듈 import
from config import MAX_TICKERS, RESULT_TYPES, API_LIMIT
from api_handler import fetch_stock_data
from portfolio_analyzer import classify_portfolio

# --- 페이지 설정 및 CSS ---
st.set_page_config(page_title="My 포트폴리오 분석기", page_icon="💡", layout="wide")

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
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False # 분석 완료 상태 추적
if 'results' not in st.session_state:
    st.session_state.results = {} # 분석 결과를 저장할 변수

# --- 사이드바 ---
st.sidebar.header("⚙️ 앱 현황 (현재 세션)")
st.sidebar.markdown("##### API 사용량")
progress = st.session_state.api_calls / API_LIMIT
st.sidebar.progress(progress)
st.sidebar.markdown(f"**{st.session_state.api_calls} / {API_LIMIT}** 호출")
st.sidebar.warning("이 카운터는 현재 세션에서만 유효하며, 브라우저를 새로고침하면 초기화됩니다.")


# --- 앱 제목 및 UI ---
st.title("💡 My 포트폴리오 분석기")
st.markdown("종목, 보유 수량, 평균 매수 단가를 목록에 추가하고, 원할 때 '분석 실행' 버튼을 눌러주세요.")

# --- 1. 포트폴리오 구성 ---
st.subheader("1. 포트폴리오 구성하기", divider="gray")

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
    add_button = st.button("목록에 추가", use_container_width=True)

if add_button and ticker:
    st.session_state.analysis_done = False # 새로운 종목 추가 시, 이전 분석 결과는 숨김
    is_already_in = any(item['ticker'] == ticker for item in st.session_state.portfolio)
    if is_already_in:
        st.warning(f"티커 '{ticker}'는 이미 목록에 있습니다.")
    else:
        new_stock = {'ticker': ticker, 'quantity': quantity, 'avg_price': avg_price}
        st.session_state.portfolio.append(new_stock)
        st.rerun()

# --- 현재 구성된 포트폴리오 목록 ---
# 분석이 완료되지 않았을 때만 상단 테이블을 보여줌
if st.session_state.portfolio and not st.session_state.analysis_done:
    st.markdown("##### 현재 구성된 포트폴리오")
    df_portfolio = pd.DataFrame(st.session_state.portfolio)
    st.dataframe(df_portfolio, use_container_width=True, hide_index=True,
                 column_config={"avg_price": st.column_config.NumberColumn(format="$%.2f")})
    
    if st.button("목록 초기화", type="secondary"):
        st.session_state.portfolio = []
        st.session_state.analysis_done = False # 초기화 시 분석 상태도 리셋
        st.rerun()

st.markdown("---")

# --- 2. 분석 실행 버튼 ---
if st.session_state.portfolio:
    required_calls = len(st.session_state.portfolio)
    
    if st.button(f"📊 {required_calls}개 종목 분석 실행 (API {required_calls}회 사용)", use_container_width=True, type="primary"):
        st.session_state.analysis_done = False # 분석 버튼 누를 때마다 이전 결과 초기화
        
        if (st.session_state.api_calls + required_calls) > API_LIMIT:
            st.error(f"분석에 필요한 API 호출 횟수({required_calls}회)가 남은 한도({API_LIMIT - st.session_state.api_calls}회)를 초과합니다.")
        else:
            with st.spinner(f"{required_calls}개 종목의 최신 정보를 API로 불러오는 중..."):
                
                fetched_data = {}
                for item in st.session_state.portfolio:
                    stock_info = fetch_stock_data(item['ticker'])
                    if stock_info:
                        fetched_data[item['ticker']] = stock_info
                
                st.session_state.api_calls += len(fetched_data)
                
                final_portfolio_data = []
                for item in st.session_state.portfolio:
                    if item['ticker'] in fetched_data:
                        final_portfolio_data.append({
                            'stock': fetched_data[item['ticker']],
                            'quantity': item['quantity'],
                            'avg_price': item['avg_price']
                        })

                if not final_portfolio_data:
                    st.error("분석할 유효한 종목 정보를 가져오지 못했습니다.")
                else:
                    final_type, sector_values, total_value = classify_portfolio(final_portfolio_data)
                    
                    # 분석 결과를 session_state에 저장
                    st.session_state.results = {
                        'final_type': final_type,
                        'sector_values': sector_values,
                        'total_value': total_value,
                        'final_portfolio_data': final_portfolio_data
                    }
                    st.session_state.analysis_done = True
                    st.rerun() # 분석 후 한번 새로고침하여 결과 표시

# --- 3. 분석 결과 표시 ---
if st.session_state.analysis_done:
    results = st.session_state.results
    final_type = results.get('final_type')
    sector_values = results.get('sector_values', {})
    total_value = results.get('total_value', 0)
    final_portfolio_data = results.get('final_portfolio_data', [])

    st.subheader("💡 분석 결과", divider="rainbow")
    
    # 상세 현황 테이블과 심층 분석 결과를 두 개의 열로 나눔
    result_cols = st.columns([3, 2]) # 너비 비율 조정

    with result_cols[0]:
        st.markdown("##### 상세 보유 현황")
        display_data = []
        for item in final_portfolio_data:
            stock = item['stock']
            current_price = stock.get('price', 0)
            value = current_price * item['quantity']
            purchase_cost = item['avg_price'] * item['quantity']
            profit_loss = value - purchase_cost
            return_rate = (profit_loss / purchase_cost) * 100 if purchase_cost > 0 else 0
            display_data.append({
                "티커": item['ticker'], "현재가": current_price, "평가액": value,
                "수익률(%)": return_rate, "평가 손익": profit_loss
            })
        df_detail = pd.DataFrame(display_data)
        st.dataframe(df_detail, use_container_width=True, hide_index=True,
                        column_config={
                            "현재가": st.column_config.NumberColumn(format="$%.2f"),
                            "평가액": st.column_config.NumberColumn(format="$%.2f"),
                            "평가 손익": st.column_config.NumberColumn(format="$%.2f"),
                            "수익률(%)": st.column_config.ProgressColumn(
                                format="%.2f%%", min_value=-100, max_value=100,
                                help="매수 평균가 대비 수익률입니다."
                            )
                        })

    with result_cols[1]:
        st.markdown("##### 심층 분석")
        
        # 메트릭 표시
        total_purchase_cost = sum(item['avg_price'] * item['quantity'] for item in final_portfolio_data)
        total_profit_loss = total_value - total_purchase_cost
        total_return_rate = (total_profit_loss / total_purchase_cost) * 100 if total_purchase_cost > 0 else 0
        
        metric_cols = st.columns(2)
        metric_cols[0].metric(label="현재 총 평가액", value=f"${total_value:,.2f}")
        metric_cols[1].metric(label="총 평가 손익", value=f"${total_profit_loss:,.2f}", delta=f"{total_return_rate:.2f}%")

        # 포트폴리오 성향 표시
        st.markdown("###### 포트폴리오 성향")
        result_info = RESULT_TYPES[final_type]
        st.write(f"**{result_info['name']}**")
        st.caption(result_info['desc'])
        
        # 섹터 분포 차트 표시
        st.markdown("###### 섹터별 자산 분포")
        if sector_values:
            fig = px.pie(names=list(sector_values.keys()), values=list(sector_values.values()), hole=0.5)
            fig.update_traces(textposition='inside', textinfo='label', showlegend=False, textfont_size=12)
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# 시작 안내 메시지 (포트폴리오가 비어있을 때만 표시)
elif not st.session_state.portfolio:
    st.info("종목을 목록에 추가한 후, '분석 실행' 버튼을 눌러주세요.")