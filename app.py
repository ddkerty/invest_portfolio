# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# 다른 모듈에서 필요한 함수와 변수들을 가져옵니다.
from config import MAX_TICKERS, RESULT_TYPES
from api_handler import fetch_stock_data
from portfolio_analyzer import classify_portfolio

# --- 페이지 기본 설정 및 CSS 스타일 주입 ---
st.set_page_config(
    page_title="My 포트폴리오 대시보드",
    page_icon="🚀",
    layout="wide"
)

# CSS를 직접 주입하여 UI를 꾸밉니다.
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# style.css 파일을 만들거나, 아래 css_string을 직접 사용합니다.
css_string = """
/* Card 스타일 */
div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
/* 버튼 스타일 */
button[data-testid="baseButton-secondary"] {
    background-color: #f0f2f6;
    color: #333;
}
"""
st.markdown(f"<style>{css_string}</style>", unsafe_allow_html=True)


# --- 세션 상태(Session State) 초기화 ---
# 앱이 재실행되어도 입력 데이터를 유지하기 위해 사용합니다.
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 앱 제목 ---
st.title("미국 포트폴리오 분석기")
st.markdown("종목, 보유 수량, 평균 매수 단가를 입력하고 포트폴리오를 정밀 분석해보세요.")

# --- 1. 입력 구간 (개선된 UX) ---
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
    # 버튼을 중앙에 위치시키기 위한 빈 공간
    st.write("") 
    st.write("")
    add_button = st.button("추가", use_container_width=True)

if add_button and ticker:
    # 포트폴리오에 새 종목 추가
    new_stock = {'ticker': ticker, 'quantity': quantity, 'avg_price': avg_price}
    st.session_state.portfolio.append(new_stock)

# --- 현재 포트폴리오 목록 표시 ---
if st.session_state.portfolio:
    st.markdown("##### 현재 포트폴리오 목록")
    
    # 데이터프레임으로 깔끔하게 표시
    df_portfolio = pd.DataFrame(st.session_state.portfolio)
    st.dataframe(df_portfolio, use_container_width=True, hide_index=True)
    
    # 포트폴리오 초기화 버튼
    if st.button("목록 초기화", type="secondary"):
        st.session_state.portfolio = []
        st.rerun() # 앱을 새로고침하여 목록을 즉시 비움

st.markdown("---")

# --- 2. 분석 실행 버튼 ---
if st.session_state.portfolio:
    if st.button("📈 포트폴리오 정밀 분석 실행", use_container_width=True, type="primary"):
        with st.spinner("최신 시세를 반영하여 포트폴리오를 분석 중입니다..."):
            
            # --- API 호출 및 데이터 구조화 ---
            final_portfolio_data = []
            for item in st.session_state.portfolio:
                stock_info = fetch_stock_data(item['ticker'])
                if stock_info:
                    # '내 평균 매수 단가' 정보를 포함하여 최종 데이터 구조화
                    final_portfolio_data.append({
                        'stock': stock_info,
                        'quantity': item['quantity'],
                        'avg_price': item['avg_price']
                    })

            if not final_portfolio_data:
                st.error("유효한 종목 정보를 찾지 못했습니다. 티커를 확인해주세요.")
            else:
                # --- 분석 실행 ---
                final_type, sector_values, total_value = classify_portfolio(final_portfolio_data)

                # --- 3. 분석 결과 대시보드 ---
                st.subheader("📊 분석 결과 대시보드", divider="rainbow")
                
                # --- 결과 요약 ---
                summary_cols = st.columns(3)
                with summary_cols[0]:
                    st.markdown("##### 포트폴리오 성향")
                    result_info = RESULT_TYPES[final_type]
                    st.header(result_info['name'])
                    st.write(result_info['desc'])
                with summary_cols[1]:
                    st.markdown("##### 포트폴리오 가치")
                    st.metric(label="현재 총 평가액", value=f"${total_value:,.2f}")
                    
                    # 총 매수금액 및 수익률 계산
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
                
                # --- 상세 현황 및 섹터 분포 ---
                detail_cols = st.columns([3, 2]) # 60% : 40% 비율로 분할
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
                            "티커": stock.get('symbol'),
                            "보유 수량": quantity,
                            "매수 평균가": f"${avg_price:,.2f}",
                            "현재가": f"${current_price:,.2f}",
                            "평가 손익": f"${profit_loss:,.2f}",
                            "수익률(%)": f"{return_rate:.2f}%"
                        })
                    df_detail = pd.DataFrame(display_data)
                    st.dataframe(df_detail, use_container_width=True, hide_index=True)

                with detail_cols[1]:
                    st.markdown("##### 섹터별 자산 분포")
                    if sector_values:
                        fig = px.pie(names=list(sector_values.keys()), values=list(sector_values.values()), hole=0.5)
                        fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
                        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig, use_container_width=True)