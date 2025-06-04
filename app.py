# app.py

import streamlit as st
import plotly.express as px
import pandas as pd # 데이터프레임 사용을 위해 import

# 다른 모듈에서 필요한 함수와 변수들을 가져옵니다.
from config import MAX_TICKERS, RESULT_TYPES
from api_handler import fetch_stock_data
from portfolio_analyzer import classify_portfolio

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="My 포트폴리오 분석기 (정밀 분석)",
    page_icon="💎",
    layout="wide" # 더 넓은 화면 사용을 위해 layout 변경
)

# --- UI 렌더링 ---
st.title("My 포트폴리오 분석기 (정밀 분석 Ver.)")
st.markdown("보유 주식의 **티커와 수량**을 입력하여 실제 자산 배분 기준의 투자 성향을 알아보세요!")

# 입력 형식 안내 강화
input_placeholder = """예시)
AAPL, 10
MSFT, 20
JNJ, 15
"""
ticker_input = st.text_area(
    label="아래 형식에 맞게 한 줄에 하나씩 '티커, 수량'을 입력하세요.",
    placeholder=input_placeholder,
    height=150
)

if st.button("정밀 분석 시작!", use_container_width=True, type="primary"):
    
    # --- 입력값 파싱 및 유효성 검사 ---
    portfolio_items_input = []
    lines = [line.strip() for line in ticker_input.split('\n') if line.strip()]
    
    for line in lines:
        try:
            ticker, quantity_str = [item.strip() for item in line.split(',')]
            quantity = int(quantity_str)
            if quantity > 0:
                portfolio_items_input.append({'ticker': ticker.upper(), 'quantity': quantity})
        except ValueError:
            st.warning(f"잘못된 형식의 줄이 있습니다: '{line}'. '티커, 수량' 형식을 지켜주세요.")
            continue
            
    if not portfolio_items_input:
        st.warning("분석할 주식 정보를 입력해주세요.")
    elif len(portfolio_items_input) > MAX_TICKERS:
        st.error(f"최대 {MAX_TICKERS}개의 종목까지만 분석할 수 있습니다. (현재 {len(portfolio_items_input)}개 입력)")
    else:
        with st.spinner("포트폴리오 데이터를 수집하고 정밀 분석 중입니다..."):
            
            # 1. API를 통해 포트폴리오 데이터 수집 및 구조화
            portfolio_data = []
            valid_tickers_count = 0
            for item in portfolio_items_input:
                stock_info = fetch_stock_data(item['ticker'])
                if stock_info:
                    portfolio_data.append({'stock': stock_info, 'quantity': item['quantity']})
                    valid_tickers_count += 1

            if not portfolio_data:
                st.error("입력하신 티커에 대한 유효한 주식 정보를 찾지 못했습니다.")
            else:
                # 2. 수집된 데이터로 포트폴리오 분석 실행
                final_type, sector_values, total_value = classify_portfolio(portfolio_data)

                # 3. 분석 결과 출력
                st.subheader("📊 포트폴리오 정밀 분석 결과", divider="rainbow")
                
                # --- 결과 요약 ---
                col1, col2 = st.columns(2)
                with col1:
                    result_info = RESULT_TYPES[final_type]
                    st.header(result_info['name'])
                    st.write(result_info['desc'])
                with col2:
                    st.metric(label="총 포트폴리오 평가액", value=f"${total_value:,.2f}")
                    st.metric(label="총 보유 종목 수", value=f"{valid_tickers_count} 개")

                st.markdown("---")

                # --- 상세 보유 현황 (데이터프레임으로 표시) ---
                st.subheader("📋 상세 보유 현황")
                display_data = []
                for item in portfolio_data:
                    stock = item['stock']
                    quantity = item['quantity']
                    price = stock.get('price', 0)
                    value = price * quantity
                    display_data.append({
                        "티커": stock.get('symbol'),
                        "회사명": stock.get('companyName'),
                        "보유 수량": quantity,
                        "현재가": f"${price:,.2f}",
                        "평가액": f"${value:,.2f}"
                    })
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown("---")

                # --- 섹터별 자산 분포 (차트) ---
                st.subheader("🗺️ 포트폴리오 영토 현황 (자산 분포)")
                if sector_values:
                    fig = px.pie(
                        names=list(sector_values.keys()), 
                        values=list(sector_values.values()),
                        title='섹터별 자산 평가액 분포',
                        hole=0.4
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05]*len(sector_values))
                    fig.update_layout(showlegend=False, title_x=0.5)
                    st.plotly_chart(fig, use_container_width=True)