# api_handler.py

import streamlit as st
import requests

@st.cache_data(ttl=3600)  # 1시간 동안 API 응답 캐싱
def fetch_stock_data(ticker):
    """FMP API를 호출하여 특정 티커의 프로필 정보를 가져옵니다."""
    api_key = st.secrets.get("FMP_API_KEY")

    if not api_key:
        # secrets.toml에 키가 없는 경우 앱 실행을 멈추고 에러 메시지 표시
        st.error("API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
        st.stop()
        
    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # 200번대 응답이 아니면 에러 발생
        data = response.json()
        
        # API가 빈 배열을 반환하거나, 유효한 데이터가 없는 경우 처리
        if data and isinstance(data, list) and data[0].get('symbol'):
            return data[0]
        else:
            st.warning(f"`{ticker}`에 대한 유효한 데이터가 없습니다. 티커를 확인해주세요.")
            return None
            
    except requests.exceptions.RequestException as e:
        st.warning(f"`{ticker}` 데이터 조회 실패: 네트워크 또는 API 서버에 문제가 있을 수 있습니다.")
        return None
    except (IndexError, KeyError):
        st.warning(f"`{ticker}`에 대한 응답 형식이 올바르지 않습니다.")
        return None