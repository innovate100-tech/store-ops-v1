"""
대시보드 메트릭 계산
"""
import streamlit as st
import pandas as pd
import datetime as dt
from datetime import timedelta
import time
from src.storage_supabase import load_csv
from src.utils.time_utils import today_kst
from src.utils.boot_perf import record_compute_call
from src.utils.cache_tokens import get_data_version
from src.ui_helpers import safe_get_value
from src.analytics import merge_sales_visitors, calculate_menu_cost


# ========== 캐시된 계산 함수들 (version_token 기반) ==========
@st.cache_data(ttl=300)  # 5분 캐시
def compute_merged_sales_visitors(store_id: str, start_date: dt.date, end_date: dt.date, v_sales: int, v_visitors: int) -> pd.DataFrame:
    """
    매출과 방문자 데이터 통합 (캐시됨, version_token 기반)
    
    Args:
        store_id: 매장 ID
        start_date: 시작 날짜
        end_date: 종료 날짜
        v_sales: sales 데이터 버전 토큰
        v_visitors: visitors 데이터 버전 토큰
    
    Returns:
        통합된 DataFrame
    """
    # 내부에서 데이터 로드 (이미 cache_data된 로더 사용)
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    
    return merge_sales_visitors(sales_df, visitors_df)


@st.cache_data(ttl=300)  # 5분 캐시
def compute_monthly_summary(store_id: str, start_date: dt.date, end_date: dt.date, v_sales: int, v_visitors: int) -> pd.DataFrame:
    """
    월별 집계 계산 (캐시됨, version_token 기반)
    
    Args:
        store_id: 매장 ID
        start_date: 시작 날짜 (6개월 전)
        end_date: 종료 날짜
        v_sales: sales 데이터 버전 토큰
        v_visitors: visitors 데이터 버전 토큰
    
    Returns:
        월별 집계 DataFrame
    """
    # 내부에서 데이터 로드 및 통합
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    
    merged_df = merge_sales_visitors(sales_df, visitors_df)
    
    # 날짜 컬럼을 datetime으로 변환
    if not merged_df.empty and '날짜' in merged_df.columns:
        merged_df['날짜'] = pd.to_datetime(merged_df['날짜'])
    
    recent_6m_data = merged_df[merged_df['날짜'].dt.date >= start_date].copy()
    if recent_6m_data.empty:
        return pd.DataFrame()
    
    recent_6m_data['연도'] = recent_6m_data['날짜'].dt.year
    recent_6m_data['월'] = recent_6m_data['날짜'].dt.month
    
    monthly_summary = recent_6m_data.groupby(['연도', '월']).agg({
        '총매출': ['sum', 'mean', 'count'],
        '방문자수': ['sum', 'mean']
    }).reset_index()
    monthly_summary.columns = ['연도', '월', '월총매출', '일평균매출', '영업일수', '월총방문자', '일평균방문자']
    monthly_summary['월별객단가'] = monthly_summary['월총매출'] / monthly_summary['월총방문자']
    monthly_summary = monthly_summary.sort_values(['연도', '월'], ascending=[False, False])
    monthly_summary['전월대비'] = monthly_summary['월총매출'].pct_change() * 100
    
    return monthly_summary


@st.cache_data(ttl=300)  # 5분 캐시
def compute_menu_sales_summary(
    store_id: str,
    start_date: dt.date,
    end_date: dt.date,
    v_sales: int,
    v_menus: int,
    v_cost: int
) -> pd.DataFrame:
    """
    메뉴별 판매 집계 및 조인 (캐시됨, version_token 기반)
    
    Args:
        store_id: 매장 ID
        start_date: 시작 날짜
        end_date: 종료 날짜
        v_sales: sales 데이터 버전 토큰
        v_menus: menus 데이터 버전 토큰
        v_cost: cost 데이터 버전 토큰
    
    Returns:
        메뉴별 집계 DataFrame
    """
    # 내부에서 데이터 로드 (이미 cache_data된 로더 사용)
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    # 날짜 변환 및 필터링
    if not daily_sales_df.empty:
        daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
        filtered_sales_df = daily_sales_df[
            (daily_sales_df['날짜'].dt.date >= start_date) & 
            (daily_sales_df['날짜'].dt.date <= end_date)
        ].copy()
    else:
        filtered_sales_df = pd.DataFrame()
    
    if filtered_sales_df.empty:
        return pd.DataFrame()
    
    # 원가 정보 계산
    cost_df = pd.DataFrame()
    if not recipe_df.empty and not ingredient_df.empty:
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
    
    # 메뉴별 총 판매수량 집계
    sales_summary = (
        filtered_sales_df.groupby('메뉴명')['판매수량']
        .sum()
        .reset_index()
    )
    sales_summary.columns = ['메뉴명', '판매수량']
    
    # 메뉴 마스터와 조인하여 판매가 가져오기
    summary_df = pd.merge(
        sales_summary,
        menu_df[['메뉴명', '판매가']],
        on='메뉴명',
        how='left',
    )
    
    # 매출 금액 계산
    summary_df['매출'] = summary_df['판매수량'] * summary_df['판매가']
    
    # 원가 정보 계산
    if not cost_df.empty:
        summary_df = pd.merge(
            summary_df,
            cost_df[['메뉴명', '원가']],
            on='메뉴명',
            how='left',
        )
        summary_df['원가'] = summary_df['원가'].fillna(0)
        summary_df['총판매원가'] = summary_df['판매수량'] * summary_df['원가']
        summary_df['이익'] = summary_df['매출'] - summary_df['총판매원가']
        summary_df['이익률'] = (summary_df['이익'] / summary_df['매출'] * 100).round(2)
        summary_df['원가율'] = (summary_df['원가'] / summary_df['판매가'] * 100).round(2)
    else:
        summary_df['원가'] = 0
        summary_df['총판매원가'] = 0
        summary_df['이익'] = summary_df['매출']
        summary_df['이익률'] = 0
        summary_df['원가율'] = 0
    
    return summary_df


def _compute_dashboard_metrics(ctx, raw_data):
    """대시보드 메트릭 계산 (손익분기점, 매출 통합, 집계 등)"""
    expense_df = raw_data['expense_df']
    targets_df = raw_data['targets_df']
    
    # 고정비 계산 (임차료, 인건비, 공과금)
    fixed_costs = 0
    if not expense_df.empty:
        fixed_categories = ['임차료', '인건비', '공과금']
        fixed_costs = expense_df[expense_df['category'].isin(fixed_categories)]['amount'].sum()
    
    # 변동비율 계산 (재료비, 부가세&카드수수료)
    variable_cost_rate = 0.0
    if not expense_df.empty:
        variable_categories = ['재료비', '부가세&카드수수료']
        variable_df = expense_df[expense_df['category'].isin(variable_categories)]
        if not variable_df.empty:
            variable_cost_rate = variable_df['amount'].sum()
    
    # 손익분기점 계산
    breakeven_sales = None
    if fixed_costs > 0 and variable_cost_rate > 0 and variable_cost_rate < 100:
        variable_rate_decimal = variable_cost_rate / 100
        if variable_rate_decimal < 1 and (1 - variable_rate_decimal) > 0:
            breakeven_sales = fixed_costs / (1 - variable_rate_decimal)
    
    # 목표 매출
    target_sales = 0
    if not targets_df.empty:
        target_row = targets_df[(targets_df['연도'] == ctx['year']) & (targets_df['월'] == ctx['month'])]
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
    # 평일/주말 비율 (기본값: 70/30)
    weekday_ratio = 70.0
    weekend_ratio = 30.0
    
    # 일일 손익분기 매출 계산
    weekday_daily_breakeven = None
    weekend_daily_breakeven = None
    weekday_daily_target = 0
    weekend_daily_target = 0
    weekday_daily_fixed = 0
    weekend_daily_fixed = 0
    weekday_daily_target_profit = 0
    weekend_daily_target_profit = 0
    target_profit = 0
    
    if breakeven_sales is not None and breakeven_sales > 0:
        weekday_daily_breakeven = (breakeven_sales * weekday_ratio / 100) / 22
        weekend_daily_breakeven = (breakeven_sales * weekend_ratio / 100) / 8
        
        if target_sales > 0:
            weekday_daily_target = (target_sales * weekday_ratio / 100) / 22
            weekend_daily_target = (target_sales * weekend_ratio / 100) / 8
        
        weekday_monthly_fixed = fixed_costs * (22 / 30)
        weekend_monthly_fixed = fixed_costs * (8 / 30)
        weekday_daily_fixed = weekday_monthly_fixed / 22
        weekend_daily_fixed = weekend_monthly_fixed / 8
        
        variable_rate_decimal = variable_cost_rate / 100
        if target_sales > 0:
            weekday_daily_target_profit = (weekday_daily_target * (1 - variable_rate_decimal)) - weekday_daily_fixed
            weekend_daily_target_profit = (weekend_daily_target * (1 - variable_rate_decimal)) - weekend_daily_fixed
            target_profit = (target_sales * (1 - variable_rate_decimal)) - fixed_costs
    
    # 매출 데이터 통합 및 집계
    v_sales = get_data_version("sales")
    v_visitors = get_data_version("visitors")
    start_date = dt.date(2020, 1, 1)
    end_date = today_kst()
    
    t0 = time.perf_counter()
    merged_df = compute_merged_sales_visitors(ctx['store_id'], start_date, end_date, v_sales, v_visitors)
    t1 = time.perf_counter()
    record_compute_call("dashboard: merge_sales_visitors", (t1 - t0) * 1000, 
                      rows_in=len(raw_data['sales_df']) + len(raw_data['visitors_df']), 
                      rows_out=len(merged_df), note="cached_token")
    
    # 날짜 컬럼을 datetime으로 변환
    if not merged_df.empty and '날짜' in merged_df.columns:
        merged_df['날짜'] = pd.to_datetime(merged_df['날짜'])
    
    # 이번달 데이터 필터링
    month_data = merged_df[
        (merged_df['날짜'].dt.year == ctx['year']) & 
        (merged_df['날짜'].dt.month == ctx['month'])
    ].copy() if not merged_df.empty else pd.DataFrame()
    
    month_total_sales = month_data['총매출'].sum() if not month_data.empty and '총매출' in month_data.columns else 0
    month_total_visitors = month_data['방문자수'].sum() if not month_data.empty and '방문자수' in month_data.columns else 0
    
    # 월별 요약 (최근 6개월)
    today = today_kst()
    six_months_ago = today - timedelta(days=180)
    
    t0 = time.perf_counter()
    monthly_summary = compute_monthly_summary(ctx['store_id'], six_months_ago, today, v_sales, v_visitors)
    t1 = time.perf_counter()
    if not monthly_summary.empty:
        record_compute_call("dashboard: monthly_summary_groupby", (t1 - t0) * 1000,
                          rows_in=len(merged_df), rows_out=len(monthly_summary), note="cached_token")
    
    # 메뉴별 판매 집계
    start_of_month = dt.date(ctx['year'], ctx['month'], 1)
    if ctx['month'] < 12:
        next_month_first = dt.date(ctx['year'], ctx['month'] + 1, 1)
        days_in_month = (next_month_first - timedelta(days=1)).day
    else:
        days_in_month = 31
    end_of_month = dt.date(ctx['year'], ctx['month'], days_in_month)
    
    v_menus = get_data_version("menus")
    v_cost = get_data_version("cost")
    
    menu_sales_summary = pd.DataFrame()
    if not raw_data['daily_sales_df'].empty:
        daily_sales_df = raw_data['daily_sales_df'].copy()
        daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
        filtered_sales_df = daily_sales_df[
            (daily_sales_df['날짜'].dt.date >= start_of_month) & 
            (daily_sales_df['날짜'].dt.date <= end_of_month)
        ].copy()
        
        if not filtered_sales_df.empty:
            t0 = time.perf_counter()
            menu_sales_summary = compute_menu_sales_summary(ctx['store_id'], start_of_month, end_of_month, v_sales, v_menus, v_cost)
            t1 = time.perf_counter()
            record_compute_call("dashboard: menu_sales_summary", (t1 - t0) * 1000,
                              rows_in=len(filtered_sales_df), rows_out=len(menu_sales_summary), note="cached_token")
    
    return {
        'fixed_costs': fixed_costs,
        'variable_cost_rate': variable_cost_rate,
        'breakeven_sales': breakeven_sales,
        'target_sales': target_sales,
        'weekday_ratio': weekday_ratio,
        'weekend_ratio': weekend_ratio,
        'weekday_daily_breakeven': weekday_daily_breakeven,
        'weekend_daily_breakeven': weekend_daily_breakeven,
        'weekday_daily_target': weekday_daily_target,
        'weekend_daily_target': weekend_daily_target,
        'weekday_daily_fixed': weekday_daily_fixed,
        'weekend_daily_fixed': weekend_daily_fixed,
        'weekday_daily_target_profit': weekday_daily_target_profit,
        'weekend_daily_target_profit': weekend_daily_target_profit,
        'target_profit': target_profit,
        'merged_df': merged_df,
        'month_data': month_data,
        'month_total_sales': month_total_sales,
        'month_total_visitors': month_total_visitors,
        'monthly_summary': monthly_summary,
        'menu_sales_summary': menu_sales_summary,
    }
