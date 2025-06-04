# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# 로컬 모듈 import
from config import MAX_TICKERS, RESULT_TYPES
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
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'results' not in st.session_state:
    st.session_state.results = {}

# --- 앱 제목 및 UI ---
st.title("💡 My 포트폴리오 분석기")
st.markdown("종목, 보유 수량, 평균 매수 단가를 목록에 추가하고, '분석 실행' 버튼을 눌러주세요.")

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
    st.session_state.analysis_done = False
    is_already_in = any(item['ticker'] == ticker for item in st.session_state.portfolio)
    if is_already_in:
        st.warning(f"티커 '{ticker}'는 이미 목록에 있습니다.")
    else:
        new_stock = {'ticker': ticker, 'quantity': quantity, 'avg_price': avg_price}
        st.session_state.portfolio.append(new_stock)
        st.rerun()

# --- 현재 구성된 포트폴리오 목록 ---
if st.session_state.portfolio and not st.session_state.analysis_done:
    st.markdown("##### 현재 구성된 포트폴리오")
    df_portfolio = pd.DataFrame(st.session_state.portfolio)
    st.dataframe(df_portfolio, use_container_width=True, hide_index=True,
                 column_config={"avg_price": st.column_config.NumberColumn(format="$%.2f")})
    
    if st.button("목록 초기화", type="secondary"):
        st.session_state.portfolio = []
        st.session_state.analysis_done = False
        st.rerun()

st.markdown("---")

# --- 2. 분석 실행 버튼 ---
if st.session_state.portfolio:
    if st.button(f"📊 {len(st.session_state.portfolio)}개 종목 분석 실행", use_container_width=True, type="primary"):
        st.session_state.analysis_done = False
        
        with st.spinner(f"{len(st.session_state.portfolio)}개 종목의 최신 정보를 API로 불러오는 중..."):
            
            fetched_data = {}
            for item in st.session_state.portfolio:
                stock_info = fetch_stock_data(item['ticker'])
                if stock_info:
                    fetched_data[item['ticker']] = stock_info
            
            final_portfolio_data = []
            for item in st.session_state.portfolio:
                if item['ticker'] in fetched_data:
                    final_portfolio_data.append({
                        'stock': fetched_data[item['ticker']],
                        'quantity': item['quantity'],
                        'avg_price': item['avg_price']
                    })

            if not final_portfolio_data:
                st.error("유효한 종목 정보를 가져오지 못했습니다. API 호출 한도를 초과했을 수 있으니 잠시 후 다시 시도해주세요.")
            else:
                final_type, sector_values, total_value = classify_portfolio(final_portfolio_data)
                
                st.session_state.results = {
                    'final_type': final_type,
                    'sector_values': sector_values,
                    'total_value': total_value,
                    'final_portfolio_data': final_portfolio_data
                }
                st.session_state.analysis_done = True
                st.rerun()

# --- 3. 분석 결과 표시 ---
if st.session_state.analysis_done:
    results = st.session_state.results
    final_type = results.get('final_type')
    sector_values = results.get('sector_values', {})
    total_value = results.get('total_value', 0)
    final_portfolio_data = results.get('final_portfolio_data', [])

    st.subheader("💡 분석 결과", divider="rainbow")
    
    result_cols = st.columns([3, 2])

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
            
            # 🐞 BUG FIX: item['ticker'] -> stock.get('symbol') 로 수정
            display_data.append({
                "티커": stock.get('symbol'), 
                "현재가": current_price, 
                "평가액": value,
                "수익률(%)": return_rate, 
                "평가 손익": profit_loss
            })
        df_detail = pd.DataFrame(display_data)
        st.dataframe(df_detail, use_container_width=True, hide_index=True,
                        column_config={
                            "현재가": st.column_config.NumberColumn(format="$%.2f"),
                            "평가액": st.column_config.NumberColumn(format="$%.2f"),
                            "평가 손익": st.column_config.NumberColumn(format="$%.2f"),
                            "수익률(%)": st.column_config.ProgressColumn(format="%.2f%%", min_value=-100, max_value=100)
                        })

    with result_cols[1]:
        st.markdown("##### 심층 분석")
        total_purchase_cost = sum(item['avg_price'] * item['quantity'] for item in final_portfolio_data)
        total_profit_loss = total_value - total_purchase_cost
        total_return_rate = (total_profit_loss / total_purchase_cost) * 100 if total_purchase_cost > 0 else 0
        
        metric_cols = st.columns(2)
        metric_cols[0].metric(label="현재 총 평가액", value=f"${total_value:,.2f}")
        metric_cols[1].metric(label="총 평가 손익", value=f"${total_profit_loss:,.2f}", delta=f"{total_return_rate:.2f}%")

        st.markdown("###### 포트폴리오 성향")
        result_info = RESULT_TYPES[final_type]
        st.write(f"**{result_info['name']}**")
        st.caption(result_info['desc'])
        
        st.markdown("###### 섹터별 자산 분포")
        if sector_values:
            fig = px.pie(names=list(sector_values.keys()), values=list(sector_values.values()), hole=0.5)
            fig.update_traces(textposition='inside', textinfo='label', showlegend=False, textfont_size=12)
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

elif not st.session_state.portfolio:
    st.info("목록에 추가 버튼을 누르면 포트폴리오가 추가됩니다.")
    st.info("이후 보유 종목을 입력하면 추가로 내 포트폴리오를 추가합니다.")
    st.info("포트폴리오를 구성한 후 분석 실행 버튼을 눌러주세요. 최대 15개 종목까지 분석할 수 있습니다.")