# portfolio_analyzer.py

from config import SECTOR_WEIGHTS, BALANCED_THRESHOLD_RATIO, MIN_POINT_DIFFERENCE_FOR_BALANCED

def classify_portfolio(portfolio_data):
    """
    주식 데이터와 '수량' 정보를 받아 포트폴리오 유형과 섹터별 '자산' 분포를 분석합니다.
    portfolio_data 형식: [{'stock': stock_info, 'quantity': int}, ...]

    Returns:
        tuple: (분석된 최종 유형(str), 섹터별 자산 평가액(dict), 총 포트폴리오 평가액(float), 성향 점수(dict))
    """
    points = {"aggressive": 0, "stable": 0, "dividend": 0}
    sector_values = {}
    total_portfolio_value = 0

    # 1. 총 포트폴리오 평가액 계산
    for item in portfolio_data:
        try:
            price = float(item['stock'].get('price', 0))
            quantity = item['quantity']
            total_portfolio_value += price * quantity
        except (ValueError, TypeError):
            continue
    
    if total_portfolio_value == 0:
        return 'balanced', {}, 0, {}

    # 2. 각 종목의 평가액 비중을 기준으로 가중치 부여하여 점수 계산
    for item in portfolio_data:
        stock = item['stock']
        quantity = item['quantity']
        
        try:
            price = float(stock.get('price', 0))
            beta = float(stock.get('beta', 1.0))
            last_div = float(stock.get('lastDiv', 0))
        except (ValueError, TypeError):
            price, beta, last_div = 0, 1.0, 0

        stock_value = price * quantity
        value_weight = stock_value / total_portfolio_value

        # --- 성향 점수 계산 (가중치 적용) ---
        sector_key = stock.get('sector', 'default')
        if sector_key not in SECTOR_WEIGHTS:
            sector_key = 'default'
        
        weights = SECTOR_WEIGHTS[sector_key]
        points["aggressive"] += weights["aggressive"] * value_weight
        points["stable"] += weights["stable"] * value_weight
        points["dividend"] += weights["dividend"] * value_weight
        
        if price > 0 and last_div > 0:
            dividend_yield = last_div / price
            if dividend_yield > 0.03: points["dividend"] += 2 * value_weight
            elif dividend_yield > 0.015: points["dividend"] += 1 * value_weight
        
        if beta > 1.3: points["aggressive"] += 1 * value_weight
        elif beta > 1.1: points["aggressive"] += 0.5 * value_weight
        
        if beta < 0.8: points["stable"] += 1 * value_weight
        elif beta < 1.0: points["stable"] += 0.5 * value_weight

        display_sector = stock.get('sector') or stock.get('industry') or "N/A"
        sector_values[display_sector] = sector_values.get(display_sector, 0) + stock_value

    # 3. 최종 유형 결정
    sorted_types = sorted(points.items(), key=lambda item: item[1], reverse=True)
    
    if not sorted_types or sorted_types[0][1] == 0:
        return 'balanced', sector_values, total_portfolio_value, points

    final_type = sorted_types[0][0]
    max_points = sorted_types[0][1]

    if len(sorted_types) > 1:
        second_max_points = sorted_types[1][1]
        point_difference = max_points - second_max_points
        if point_difference < 0.1:
            final_type = 'balanced'
            
    # ❗️수정: points 딕셔너리를 마지막에 추가하여 반환
    return final_type, sector_values, total_portfolio_value, points