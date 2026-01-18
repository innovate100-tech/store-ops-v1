"""
분석 관련 함수 모듈
"""
import pandas as pd
import numpy as np


def calculate_correlation(sales_df, visitors_df):
    """
    매출과 방문자수의 상관계수 계산
    
    Args:
        sales_df: 매출 DataFrame (날짜, 총매출 컬럼 필요)
        visitors_df: 방문자 DataFrame (날짜, 방문자수 컬럼 필요)
    
    Returns:
        float: 피어슨 상관계수
    """
    if sales_df.empty or visitors_df.empty:
        return None
    
    # 날짜 기준으로 조인
    merged = pd.merge(
        sales_df[['날짜', '총매출']],
        visitors_df[['날짜', '방문자수']],
        on='날짜',
        how='inner'
    )
    
    if len(merged) < 2:
        return None
    
    # 상관계수 계산
    correlation = merged['총매출'].corr(merged['방문자수'])
    return correlation


def merge_sales_visitors(sales_df, visitors_df):
    """
    매출과 방문자 데이터를 날짜 기준으로 조인
    
    Args:
        sales_df: 매출 DataFrame
        visitors_df: 방문자 DataFrame
    
    Returns:
        pandas.DataFrame: 조인된 DataFrame
    """
    if sales_df.empty and visitors_df.empty:
        return pd.DataFrame()
    
    if sales_df.empty:
        return visitors_df.copy()
    
    if visitors_df.empty:
        return sales_df.copy()
    
    merged = pd.merge(
        sales_df,
        visitors_df,
        on='날짜',
        how='outer'
    )
    
    # 날짜 기준 정렬
    merged = merged.sort_values('날짜')
    
    return merged


def calculate_menu_cost(menu_df, recipe_df, ingredient_df):
    """
    메뉴별 원가 계산
    
    Args:
        menu_df: 메뉴 마스터 DataFrame (메뉴명, 판매가)
        recipe_df: 레시피 DataFrame (메뉴명, 재료명, 사용량)
        ingredient_df: 재료 마스터 DataFrame (재료명, 단위, 단가)
    
    Returns:
        pandas.DataFrame: 메뉴명, 판매가, 원가, 원가율 컬럼 포함
    """
    if menu_df.empty or recipe_df.empty or ingredient_df.empty:
        return pd.DataFrame(columns=['메뉴명', '판매가', '원가', '원가율'])
    
    # 레시피와 재료 마스터 조인 (재료 단가 가져오기)
    recipe_with_price = pd.merge(
        recipe_df,
        ingredient_df[['재료명', '단가']],
        on='재료명',
        how='left'
    )
    
    # 재료 단가가 없는 경우 0으로 처리
    recipe_with_price['단가'] = recipe_with_price['단가'].fillna(0)
    
    # 사용량 * 단가로 각 재료의 비용 계산
    recipe_with_price['재료비'] = recipe_with_price['사용량'] * recipe_with_price['단가']
    
    # 메뉴별 원가 합계 계산 (그룹별 합계)
    menu_costs = recipe_with_price.groupby('메뉴명')['재료비'].sum().reset_index()
    menu_costs.columns = ['메뉴명', '원가']
    
    # 메뉴 마스터와 조인 (판매가 가져오기)
    result = pd.merge(
        menu_df[['메뉴명', '판매가']],
        menu_costs,
        on='메뉴명',
        how='left'
    )
    
    # 원가가 없는 경우 0으로 처리
    result['원가'] = result['원가'].fillna(0)
    
    # 원가율 계산 (원가 / 판매가 * 100)
    result['원가율'] = (result['원가'] / result['판매가'] * 100).round(2)
    result['원가율'] = result['원가율'].fillna(0)
    
    # 원가율 높은 순 정렬
    result = result.sort_values('원가율', ascending=False)
    
    return result


def calculate_ingredient_usage(daily_sales_df, recipe_df):
    """
    재료 사용량 자동 계산
    일일 판매량 * 레시피 사용량 = 재료 사용량
    
    Args:
        daily_sales_df: 일일 판매 DataFrame (날짜, 메뉴명, 판매수량)
        recipe_df: 레시피 DataFrame (메뉴명, 재료명, 사용량)
    
    Returns:
        pandas.DataFrame: 날짜, 재료명, 총사용량 컬럼 포함
    """
    if daily_sales_df.empty or recipe_df.empty:
        return pd.DataFrame(columns=['날짜', '재료명', '총사용량'])
    
    # 일일 판매와 레시피 조인 (메뉴명 기준)
    merged = pd.merge(
        daily_sales_df[['날짜', '메뉴명', '판매수량']],
        recipe_df[['메뉴명', '재료명', '사용량']],
        on='메뉴명',
        how='inner'
    )
    
    # 재료 사용량 = 판매수량 * 레시피 사용량
    merged['재료사용량'] = merged['판매수량'] * merged['사용량']
    
    # 날짜, 재료명별로 그룹화하여 총 사용량 집계
    result = merged.groupby(['날짜', '재료명'])['재료사용량'].sum().reset_index()
    result.columns = ['날짜', '재료명', '총사용량']
    
    # 날짜 기준 정렬
    result = result.sort_values(['날짜', '재료명'])
    
    return result


def calculate_order_recommendation(
    ingredient_df, 
    inventory_df, 
    usage_df, 
    days_for_avg=7, 
    forecast_days=3
):
    """
    발주 추천 계산
    
    발주 필요량 = max(0, 안전재고 + 예상소요량 - 현재고)
    예상소요량 = 최근 N일 평균 사용량 * 예측일수
    
    Args:
        ingredient_df: 재료 마스터 DataFrame (재료명, 단위, 단가)
        inventory_df: 재고 DataFrame (재료명, 현재고, 안전재고)
        usage_df: 재료 사용량 DataFrame (날짜, 재료명, 총사용량)
        days_for_avg: 평균 사용량 계산 기간 (기본 7일)
        forecast_days: 예측일수 (기본 3일)
    
    Returns:
        pandas.DataFrame: 재료명, 단위, 현재고, 안전재고, 최근평균사용량, 예상소요량, 발주필요량, 예상금액
    """
    if ingredient_df.empty or inventory_df.empty:
        return pd.DataFrame(columns=['재료명', '단위', '현재고', '안전재고', '최근평균사용량', '예상소요량', '발주필요량', '예상금액'])
    
    # 재료 마스터와 재고 조인
    result = pd.merge(
        ingredient_df[['재료명', '단위', '단가']],
        inventory_df[['재료명', '현재고', '안전재고']],
        on='재료명',
        how='right'  # 재고가 있는 재료만
    )
    
    # 사용량 데이터가 있으면 최근 평균 사용량 계산
    if not usage_df.empty:
        # 최근 N일 데이터 추출
        usage_df['날짜'] = pd.to_datetime(usage_df['날짜'])
        max_date = usage_df['날짜'].max()
        recent_cutoff = max_date - pd.Timedelta(days=days_for_avg)
        recent_usage = usage_df[usage_df['날짜'] >= recent_cutoff]
        
        if not recent_usage.empty:
            # 재료별 최근 평균 일일 사용량 계산
            daily_avg = recent_usage.groupby('재료명')['총사용량'].sum() / days_for_avg
            daily_avg = daily_avg.reset_index()
            daily_avg.columns = ['재료명', '최근평균사용량']
            
            # 결과에 조인
            result = pd.merge(
                result,
                daily_avg,
                on='재료명',
                how='left'
            )
        else:
            result['최근평균사용량'] = 0
    else:
        result['최근평균사용량'] = 0
    
    # 예상소요량 = 최근평균사용량 * 예측일수
    result['예상소요량'] = (result['최근평균사용량'] * forecast_days).fillna(0)
    result['최근평균사용량'] = result['최근평균사용량'].fillna(0)
    
    # 발주 필요량 = max(0, 안전재고 + 예상소요량 - 현재고)
    result['발주필요량'] = (result['안전재고'] + result['예상소요량'] - result['현재고']).clip(lower=0)
    
    # 예상 금액 = 발주필요량 * 단가
    result['예상금액'] = result['발주필요량'] * result['단가']
    
    # 발주 필요량이 0보다 큰 것만 필터링하고 정렬
    result = result[result['발주필요량'] > 0].sort_values('발주필요량', ascending=False)
    
    return result


def abc_analysis(daily_sales_df, menu_df, cost_df=None, a_threshold=70, b_threshold=20, c_threshold=10):
    """
    메뉴 ABC 분석
    
    기준: 판매량 비중, 매출 비중, 공헌이익 비중
    분류: A (상위 70%), B (다음 20%), C (하위 10%)
    
    Args:
        daily_sales_df: 일일 판매 DataFrame (날짜, 메뉴명, 판매수량)
        menu_df: 메뉴 마스터 DataFrame (메뉴명, 판매가)
        cost_df: 원가 분석 DataFrame (메뉴명, 판매가, 원가, 원가율) - 선택사항
        a_threshold: A 등급 비중 (기본 70%)
        b_threshold: B 등급 비중 (기본 20%)
        c_threshold: C 등급 비중 (기본 10%)
    
    Returns:
        pandas.DataFrame: 메뉴명, 판매량, 매출, 공헌이익, 판매량비중, 매출비중, 공헌이익비중, ABC등급
    """
    if daily_sales_df.empty or menu_df.empty:
        return pd.DataFrame(columns=[
            '메뉴명', '판매량', '매출', '공헌이익', 
            '판매량비중', '매출비중', '공헌이익비중', 'ABC등급'
        ])
    
    # 일일 판매 데이터 집계 (메뉴별 총 판매량)
    sales_summary = daily_sales_df.groupby('메뉴명')['판매수량'].sum().reset_index()
    sales_summary.columns = ['메뉴명', '판매량']
    
    # 메뉴 마스터와 조인하여 판매가 가져오기
    result = pd.merge(
        sales_summary,
        menu_df[['메뉴명', '판매가']],
        on='메뉴명',
        how='left'
    )
    
    # 매출 계산 (판매량 * 판매가)
    result['매출'] = result['판매량'] * result['판매가']
    
    # 원가 정보와 조인
    if cost_df is not None and not cost_df.empty:
        result = pd.merge(
            result,
            cost_df[['메뉴명', '원가']],
            on='메뉴명',
            how='left'
        )
        result['원가'] = result['원가'].fillna(0)
    else:
        result['원가'] = 0
    
    # 공헌이익 계산 (매출 - 원가)
    result['공헌이익'] = result['매출'] - (result['판매량'] * result['원가'])
    
    # 비중 계산 (누적 비중 기준)
    total_sales_qty = result['판매량'].sum()
    total_sales_amount = result['매출'].sum()
    total_contribution = result['공헌이익'].sum()
    
    if total_sales_qty > 0:
        result['판매량비중'] = (result['판매량'] / total_sales_qty * 100).round(2)
    else:
        result['판매량비중'] = 0
    
    if total_sales_amount > 0:
        result['매출비중'] = (result['매출'] / total_sales_amount * 100).round(2)
    else:
        result['매출비중'] = 0
    
    if total_contribution > 0:
        result['공헌이익비중'] = (result['공헌이익'] / total_contribution * 100).round(2)
    else:
        result['공헌이익비중'] = 0
    
    # ABC 등급 결정 (공헌이익 비중 기준으로 정렬 후 분류)
    result = result.sort_values('공헌이익비중', ascending=False).reset_index(drop=True)
    
    # 누적 비중 계산
    result['공헌이익누적비중'] = result['공헌이익비중'].cumsum()
    
    # ABC 등급 할당
    def assign_abc_grade(cumulative):
        if cumulative <= a_threshold:
            return 'A'
        elif cumulative <= a_threshold + b_threshold:
            return 'B'
        else:
            return 'C'
    
    result['ABC등급'] = result['공헌이익누적비중'].apply(assign_abc_grade)
    
    # 불필요한 컬럼 제거
    result = result.drop(['공헌이익누적비중'], axis=1)
    
    # 정렬 (ABC 등급, 공헌이익 비중)
    grade_order = {'A': 1, 'B': 2, 'C': 3}
    result['등급순서'] = result['ABC등급'].map(grade_order)
    result = result.sort_values(['등급순서', '공헌이익비중'], ascending=[True, False])
    result = result.drop(['등급순서'], axis=1)
    
    return result


def target_gap_analysis(sales_df, targets_df, cost_df, year, month, daily_sales_df=None, menu_df=None):
    """
    목표 대비 분석 (판매 비중 반영한 원가율 계산)
    
    Args:
        sales_df: 매출 DataFrame (날짜, 총매출)
        targets_df: 목표 DataFrame (연도, 월, 목표매출, 목표원가율, ...)
        cost_df: 원가 분석 DataFrame (메뉴명, 판매가, 원가, 원가율)
        year: 분석 연도
        month: 분석 월
        daily_sales_df: 일일 판매 DataFrame (날짜, 메뉴명, 판매수량) - 판매 비중 계산용
        menu_df: 메뉴 마스터 DataFrame (메뉴명, 판매가) - 판매 비중 계산용
    
    Returns:
        dict: 분석 결과 딕셔너리
    """
    # 해당 월 목표 데이터 가져오기
    target_data = targets_df[
        (targets_df['연도'] == year) & (targets_df['월'] == month)
    ]
    
    if target_data.empty:
        return None
    
    target_row = target_data.iloc[0]
    target_sales = target_row['목표매출']
    target_cost_rate = target_row['목표원가율']
    target_profit_rate = target_row['목표순이익률']
    
    # 해당 월 매출 데이터 필터링
    sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
    month_sales = sales_df[
        (sales_df['날짜'].dt.year == year) & 
        (sales_df['날짜'].dt.month == month)
    ]
    
    # 현재 누적 매출
    current_sales = month_sales['총매출'].sum() if not month_sales.empty else 0
    
    # 목표 진행률
    progress_rate = (current_sales / target_sales * 100) if target_sales > 0 else 0
    
    # 하루 목표 매출 (월 일수 기준)
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    daily_target = target_sales / days_in_month
    
    # 현재 일수 (오늘까지)
    from datetime import datetime
    today = datetime.now()
    if today.year == year and today.month == month:
        current_day = today.day
    else:
        current_day = days_in_month
    
    # 예상 매출 (현재 일평균 * 남은 일수 + 현재 누적)
    if current_day > 0:
        daily_avg = current_sales / current_day
        remaining_days = days_in_month - current_day
        forecast_sales = current_sales + (daily_avg * remaining_days)
    else:
        forecast_sales = 0
    
    # 현재 원가율 계산 (판매 비중 반영한 가중 평균)
    current_cost_rate = 0
    if not cost_df.empty:
        # daily_sales_df와 menu_df가 있으면 판매 비중 반영
        if daily_sales_df is not None and menu_df is not None and not daily_sales_df.empty:
            try:
                # 해당 월 판매 데이터 필터링
                daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
                month_daily_sales = daily_sales_df[
                    (daily_sales_df['날짜'].dt.year == year) & 
                    (daily_sales_df['날짜'].dt.month == month)
                ]
                
                if not month_daily_sales.empty:
                    # 메뉴별 판매량 집계
                    menu_sales = month_daily_sales.groupby('메뉴명')['판매수량'].sum().reset_index()
                    
                    # 메뉴 마스터와 조인하여 판매가 확인
                    menu_sales = menu_sales.merge(menu_df[['메뉴명', '판매가']], on='메뉴명', how='left')
                    menu_sales['매출'] = menu_sales['판매수량'] * menu_sales['판매가']
                    
                    # 원가 정보와 조인
                    menu_sales = menu_sales.merge(
                        cost_df[['메뉴명', '원가', '원가율']], 
                        on='메뉴명', 
                        how='left'
                    )
                    
                    # 매출 비중 계산
                    total_revenue = menu_sales['매출'].sum()
                    if total_revenue > 0:
                        menu_sales['매출비중'] = menu_sales['매출'] / total_revenue
                        # 가중 평균 원가율 계산
                        current_cost_rate = (menu_sales['원가율'] * menu_sales['매출비중']).sum()
                    else:
                        # 매출이 없으면 평균 원가율 사용
                        current_cost_rate = cost_df['원가율'].mean()
                else:
                    # 판매 데이터가 없으면 평균 원가율 사용
                    current_cost_rate = cost_df['원가율'].mean()
            except Exception:
                # 오류 발생 시 평균 원가율 사용
                current_cost_rate = cost_df['원가율'].mean()
        else:
            # 판매 데이터가 없으면 평균 원가율 사용
            current_cost_rate = cost_df['원가율'].mean()
    
    # 원가율 차이
    cost_rate_gap = current_cost_rate - target_cost_rate
    
    # 예상 이익
    forecast_profit = forecast_sales * (target_profit_rate / 100)
    
    # 신호등 판단
    def get_status_indicator(progress, cost_gap):
        if progress >= 100 and cost_gap <= 5:
            return ('정상', '🟢')
        elif progress >= 80 or (progress >= 50 and cost_gap <= 10):
            return ('주의', '🟡')
        else:
            return ('위험', '🔴')
    
    status, indicator = get_status_indicator(progress_rate, cost_rate_gap)
    
    return {
        'target_sales': target_sales,
        'current_sales': current_sales,
        'progress_rate': progress_rate,
        'daily_target': daily_target,
        'forecast_sales': forecast_sales,
        'forecast_profit': forecast_profit,
        'target_cost_rate': target_cost_rate,
        'current_cost_rate': current_cost_rate,
        'cost_rate_gap': cost_rate_gap,
        'status': status,
        'indicator': indicator,
        'days_in_month': days_in_month,
        'current_day': current_day
    }
