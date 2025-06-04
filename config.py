# config.py

# 최대 분석 가능 티커 개수
MAX_TICKERS = 15

# 밸런스형 포트폴리오 판단 기준 상수
BALANCED_THRESHOLD_RATIO = 0.2
MIN_POINT_DIFFERENCE_FOR_BALANCED = 2

# 분석에 사용될 섹터별 가중치
# FMP API와 GICS 표준 이름을 모두 포함하여 유연성 확보
SECTOR_WEIGHTS = {
    "Technology":               {"aggressive": 2, "stable": 1, "dividend": 0},
    "Consumer Discretionary":   {"aggressive": 3, "stable": 0, "dividend": 0}, # Consumer Cyclical
    "Communication Services":   {"aggressive": 2, "stable": 1, "dividend": 0},
    "Health Care":              {"aggressive": 1, "stable": 2, "dividend": 0},
    "Financial Services":       {"aggressive": 1, "stable": 1, "dividend": 1}, # FMP
    "Financials":               {"aggressive": 1, "stable": 1, "dividend": 1}, # GICS
    "Industrials":              {"aggressive": 1, "stable": 1, "dividend": 1},
    "Consumer Staples":         {"aggressive": 0, "stable": 2, "dividend": 1}, # Consumer Defensive
    "Utilities":                {"aggressive": 0, "stable": 2, "dividend": 1},
    "Real Estate":              {"aggressive": 0, "stable": 1, "dividend": 2},
    "Energy":                   {"aggressive": 1, "stable": 0, "dividend": 2},
    "Basic Materials":          {"aggressive": 1, "stable": 1, "dividend": 1}, # FMP
    "Materials":                {"aggressive": 1, "stable": 1, "dividend": 1}, # GICS
    "N/A":                      {"aggressive": 1, "stable": 1, "dividend": 1},
    "Other":                    {"aggressive": 1, "stable": 1, "dividend": 1},
    "default":                  {"aggressive": 1, "stable": 1, "dividend": 1}
}

# 결과 유형별 아이콘, 이름, 설명
RESULT_TYPES = {
    "aggressive": {
        "name": "🚀 공격형 포트폴리오",
        "desc": "높은 리스크를 감수하며 시장을 뛰어넘는 성장을 추구합니다. 미래를 바꾸는 혁신 기업들이 당신의 포트폴리오를 이끌고 있습니다."
    },
    "stable": {
        "name": "🛡️ 안정형 포트폴리오",
        "desc": "시장의 변동성 속에서도 굳건히 자산을 지켜내는 것을 최우선으로 합니다. 꾸준함이 당신의 가장 큰 무기입니다."
    },
    "dividend": {
        "name": "💎 배당형 포트폴리오",
        "desc": "화려한 성장보다는 꾸준히 쌓이는 현금 흐름의 가치를 압니다. 당신의 포트폴리오는 시간이 지날수록 부유해집니다."
    },
    "balanced": {
        "name": "⚖️ 밸런스형 포트폴리오",
        "desc": "성장과 안정, 두 마리 토끼를 모두 잡으려 합니다. 어떤 시장 상황에서도 유연하게 대처할 수 있는 지혜로운 포트폴리오입니다."
    }
}

# 하루 API 호출 제한
API_LIMIT = 250