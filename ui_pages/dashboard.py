"""
통합 대시보드 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import datetime as dt
from datetime import timedelta
from calendar import monthrange
import time
from src.ui_helpers import render_page_header, safe_get_value
from src.ui.aggrid_render import render_aggrid
from src.utils.time_utils import current_year_kst, current_month_kst, today_kst, now_kst
from src.storage_supabase import load_csv, load_expense_structure
from src.analytics import merge_sales_visitors, calculate_menu_cost, calculate_ingredient_usage
from src.utils.boot_perf import record_compute_call
from src.utils.cache_tokens import get_data_version
from src.auth import get_current_store_id as _get_current_store_id

# 쿼리 진단 함수
def _show_query_diagnostics():
    """대시보드 페이지에서 사용하는 실제 쿼리 정보 출력"""
    try:
        from src.auth import get_current_store_id, get_supabase_client
        from src.storage_supabase import get_read_client
        
        store_id = get_current_store_id()
        st.write(f"**사용된 store_id:** `{store_id}`")
        
        current_year = current_year_kst()
        current_month = current_month_kst()
        st.write(f"**필터 값:** 연도={current_year}, 월={current_month}")
        
        st.divider()
        st.write("**실제 쿼리 실행 결과:**")
        
        # 1. load_csv 호출 테스트 (menu_master)
        st.write("**1. menu_master 테이블 조회:**")
        try:
            menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
            st.write(f"- Row count: {len(menu_df)}")
            if not menu_df.empty:
                st.write("- 첫 row 샘플:")
                st.json(menu_df.iloc[0].to_dict())
            else:
                st.warning("⚠️ 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
        
        st.divider()
        
        # 2. load_expense_structure 호출 테스트
        st.write("**2. expense_structure 테이블 조회:**")
        try:
            expense_df = load_expense_structure(current_year, current_month)
            st.write(f"- Row count: {len(expense_df)}")
            if not expense_df.empty:
                st.write("- 첫 row 샘플:")
                st.json(expense_df.iloc[0].to_dict())
            else:
                st.warning("⚠️ 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
        
        st.divider()
        
        # 3. 직접 Supabase 쿼리 테스트
        st.write("**3. 직접 Supabase 쿼리 (menu_master):**")
        try:
            supabase = get_read_client()
            if supabase and store_id:
                result = supabase.table("menu_master").select("*").eq("store_id", store_id).limit(5).execute()
                st.write(f"- Row count: {len(result.data) if result.data else 0}")
                if result.data:
                    st.write("- 첫 row 샘플:")
                    st.json(result.data[0])
                else:
                    st.warning("⚠️ 데이터가 비어있습니다.")
            else:
                st.error("❌ Supabase 클라이언트 또는 store_id가 없습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
        
        st.divider()
        
        # 4. targets 테이블 조회
        st.write("**4. targets 테이블 조회:**")
        try:
            targets_df = load_csv('targets.csv', default_columns=[
                '연도', '월', '목표매출', '목표원가율', '목표인건비율',
                '목표임대료율', '목표기타비용율', '목표순이익률'
            ])
            filtered_df = targets_df[(targets_df['연도'] == current_year) & (targets_df['월'] == current_month)]
            st.write(f"- 전체 Row count: {len(targets_df)}")
            st.write(f"- 필터링 후 Row count (연도={current_year}, 월={current_month}): {len(filtered_df)}")
            if not filtered_df.empty:
                st.write("- 첫 row 샘플:")
                st.json(filtered_df.iloc[0].to_dict())
            else:
                st.warning("⚠️ 필터링된 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            
    except Exception as e:
        st.error(f"진단 중 오류 발생: {type(e).__name__}: {str(e)}")
        st.exception(e)

# perf_span import (fallback 포함)
try:
    from src.utils.boot_perf import perf_span
except ImportError:
    # fallback: perf_span이 없으면 빈 컨텍스트 매니저 제공
    from contextlib import contextmanager
    @contextmanager
    def perf_span(*args, **kwargs):
        yield

# 공통 설정 적용
bootstrap(page_title="Dashboard")


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
    
    from src.analytics import merge_sales_visitors
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
    
    from src.analytics import merge_sales_visitors
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


def render_dashboard():
    """통합 대시보드 페이지 렌더링"""
    render_page_header("통합 대시보드", "📊")
    
    # 쿼리 로그 출력 (DEV 박스)
    with st.expander("🔍 쿼리 진단 정보 (DEV)", expanded=False):
        _show_query_diagnostics()
    
    # dev_mode에서 store_id 표시 (선택)
    try:
        from src.auth import is_dev_mode
        if is_dev_mode():
            store_id_debug = _get_current_store_id() or "default"
            with st.sidebar.expander("🔧 디버그 정보", expanded=False):
                st.caption(f"store_id: {store_id_debug}")
    except Exception:
        pass
    
    current_year = current_year_kst()
    current_month = current_year_kst()
    
    # ========== 손익분기 매출 vs 목표 매출 비교 ==========
    expense_df = load_expense_structure(current_year, current_month)
    
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
    
    # 목표 매출 로드
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    
    target_sales = 0
    if not targets_df.empty:
        target_row = targets_df[(targets_df['연도'] == current_year) & (targets_df['월'] == current_month)]
        # Phase 1: 안전한 DataFrame 접근
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
    # 평일/주말 비율 (기본값: 70/30)
    weekday_ratio = 70.0
    weekend_ratio = 30.0
    
    if breakeven_sales is not None and breakeven_sales > 0:
        # 일일 손익분기 매출 계산
        weekday_daily_breakeven = (breakeven_sales * weekday_ratio / 100) / 22
        weekend_daily_breakeven = (breakeven_sales * weekend_ratio / 100) / 8
        
        # 일일 목표 매출 계산
        weekday_daily_target = 0
        weekend_daily_target = 0
        if target_sales > 0:
            weekday_daily_target = (target_sales * weekday_ratio / 100) / 22
            weekend_daily_target = (target_sales * weekend_ratio / 100) / 8
        
        # 일일 고정비 계산
        weekday_monthly_fixed = fixed_costs * (22 / 30)
        weekend_monthly_fixed = fixed_costs * (8 / 30)
        weekday_daily_fixed = weekday_monthly_fixed / 22
        weekend_daily_fixed = weekend_monthly_fixed / 8
        
        # 변동비율 소수점 변환
        variable_rate_decimal = variable_cost_rate / 100
        
        # 일일 영업이익 계산
        weekday_daily_breakeven_profit = 0
        weekend_daily_breakeven_profit = 0
        
        weekday_daily_target_profit = 0
        weekend_daily_target_profit = 0
        if target_sales > 0:
            weekday_daily_target_profit = (weekday_daily_target * (1 - variable_rate_decimal)) - weekday_daily_fixed
            weekend_daily_target_profit = (weekend_daily_target * (1 - variable_rate_decimal)) - weekend_daily_fixed
        
        # 추정 영업이익 계산
        breakeven_profit = 0
        target_profit = 0
        if target_sales > 0:
            target_profit = (target_sales * (1 - variable_rate_decimal)) - fixed_costs
        
        # 손익분기 매출 vs 목표 매출 비교 섹션
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📊 손익분기 매출 vs 목표 매출 비교
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if breakeven_sales:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.75rem;">
                <span style="color: #ffffff; font-size: 0.85rem;">
                    계산 공식: 고정비 ÷ (1 - 변동비율) = {int(fixed_costs):,}원 ÷ (1 - {variable_cost_rate:.1f}%)
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # 월간 매출 비교
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                <div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">📊 손익분기 월매출</div>
                <div style="font-size: 1.5rem; font-weight: 700;">{int(breakeven_sales):,}원</div>
                <div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.6rem;">
                    💰 추정 영업이익
                </div>
                <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem;">0원</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if target_sales > 0:
                profit_color = "#ffd700" if target_profit > 0 else "#ff6b6b"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                    <div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">🎯 목표 월매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">{int(target_sales):,}원</div>
                    <div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.6rem;">
                        💰 추정 영업이익
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem; color: {profit_color};">{int(target_profit):,}원</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; text-align: center; margin-top: 0.25rem; border: 2px dashed rgba(255,255,255,0.3);">
                    <div style="font-size: 0.85rem; margin-bottom: 0.4rem; color: #ffffff;">🎯 목표 월매출</div>
                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">목표 비용구조 페이지에서 목표 매출을 설정하세요</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # 일일 매출 비교 섹션
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📅 일일 매출 비교
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            weekday_profit_color = "#ffd700" if weekday_daily_target_profit > 0 else "#ff6b6b" if weekday_daily_target_profit < 0 else "white"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 1rem; border-radius: 8px; color: white; margin-top: 0.25rem; text-align: right;">
                <div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">📅 평일 일일 매출</div>
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekday_daily_breakeven):,}원</div>
                {f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekday_daily_target):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                <div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; text-align: center;">
                    💰 일일 영업이익
                </div>
                <div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem; margin-bottom: 0.2rem;">손익분기시 영업이익: 0원</div>
                {f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekday_profit_color};">목표시 영업이익: {int(weekday_daily_target_profit):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                <div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.4rem;">
                    (월매출 × {weekday_ratio:.1f}% ÷ 22일)
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            weekend_profit_color = "#ffd700" if weekend_daily_target_profit > 0 else "#ff6b6b" if weekend_daily_target_profit < 0 else "white"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 1rem; border-radius: 8px; color: white; margin-top: 0.25rem; text-align: right;">
                <div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">🎉 주말 일일 매출</div>
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekend_daily_breakeven):,}원</div>
                {f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekend_daily_target):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                <div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; text-align: center;">
                    💰 일일 영업이익
                </div>
                <div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem; margin-bottom: 0.2rem;">손익분기시 영업이익: 0원</div>
                {f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekend_profit_color};">목표시 영업이익: {int(weekend_daily_target_profit):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                <div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.4rem;">
                    (월매출 × {weekend_ratio:.1f}% ÷ 8일)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # ========== 매출 수준별 비용·영업이익 시뮬레이션 ==========
        if target_sales > 0:
            # 5대 비용 세부 계산을 위한 카테고리별 데이터
            fixed_by_category = {
                '임차료': 0,
                '인건비': 0,
                '공과금': 0,
            }
            variable_rate_by_category = {
                '재료비': 0.0,
                '부가세&카드수수료': 0.0,
            }
            
            if not expense_df.empty:
                fixed_categories = ['임차료', '인건비', '공과금']
                for cat in fixed_categories:
                    fixed_by_category[cat] = expense_df[expense_df['category'] == cat]['amount'].sum()
                
                variable_categories = ['재료비', '부가세&카드수수료']
                variable_df = expense_df[expense_df['category'].isin(variable_categories)]
                if not variable_df.empty:
                    for cat in variable_categories:
                        variable_rate_by_category[cat] = variable_df[variable_df['category'] == cat]['amount'].sum()
            
            # 목표매출을 기준으로 다양한 시나리오 생성
            scenarios = [
                ("목표매출 - 1,000만원", max(target_sales - 10_000_000, 0)),
                ("목표매출 - 500만원", max(target_sales - 5_000_000, 0)),
                ("목표매출 (기준)", target_sales),
                ("목표매출 + 500만원", target_sales + 5_000_000),
                ("목표매출 + 1,000만원", target_sales + 10_000_000),
                ("목표매출 + 1,500만원", target_sales + 15_000_000),
            ]
            
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📊 매출 수준별 비용·영업이익 시뮬레이션
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.75rem;">
                <span style="color: #ffffff; font-size: 0.85rem;">
                    비용구조의 고정비와 변동비율, 목표 매출을 기준으로 다양한 매출 수준에서의 비용과 영업이익을 비교합니다.
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            cols = [col1, col2, col3]
            
            for idx, (label, sales) in enumerate(scenarios):
                if sales <= 0:
                    continue
                
                # 5대 비용 세부 계산
                rent_cost = fixed_by_category.get('임차료', 0)
                labor_cost = fixed_by_category.get('인건비', 0)
                utility_cost = fixed_by_category.get('공과금', 0)
                material_rate = variable_rate_by_category.get('재료비', 0.0) / 100
                fee_rate = variable_rate_by_category.get('부가세&카드수수료', 0.0) / 100
                material_cost = sales * material_rate
                fee_cost = sales * fee_rate
                
                total_cost = rent_cost + labor_cost + utility_cost + material_cost + fee_cost
                profit = sales - total_cost
                
                tile_col = cols[idx % 3]
                with tile_col:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 1rem; border-radius: 10px; margin-top: 0.5rem; color: #e5e7eb; box-shadow: 0 2px 6px rgba(0,0,0,0.35);">
                        <div style="font-size: 0.85rem; margin-bottom: 0.3rem; opacity: 0.9;">{label}</div>
                        <!-- 매출 영역: 선명한 흰색 -->
                        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem; color: #ffffff !important;">
                            매출: {int(sales):,}원
                        </div>
                        <!-- 비용 영역 제목: 더 진한 빨간색 -->
                        <div style="font-size: 0.85rem; margin-top: 0.4rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.4rem; color: #ff4d4f !important;">
                            비용 합계 및 세부내역
                        </div>
                        <!-- 총 비용: 더 진한 빨간색 -->
                        <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.15rem; color: #ff4d4f !important;">
                            총 비용: {int(total_cost):,}원
                        </div>
                        <div style="font-size: 0.75rem; margin-top: 0.25rem; line-height: 1.3; color: #ff4d4f !important;">
                            임차료(고정비): {int(rent_cost):,}원<br>
                            인건비(고정비): {int(labor_cost):,}원<br>
                            공과금(고정비): {int(utility_cost):,}원<br>
                            재료비(변동비): {int(material_cost):,}원<br>
                            부가세·카드수수료(변동비): {int(fee_cost):,}원
                        </div>
                        <!-- 추정 영업이익 제목: 선명한 노란색 -->
                        <div style="font-size: 0.85rem; margin-top: 0.4rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.4rem; color: #ffd700 !important;">
                            추정 영업이익
                        </div>
                        <!-- 추정 영업이익 값: 선명한 노란색 -->
                        <div style="font-size: 1rem; font-weight: 600; color: #ffd700 !important;">
                            {int(profit):,}원
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # ========== 매출 관리 항목들 ==========
        # 매출 데이터 로드
        sales_df_dashboard = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
        visitors_df_dashboard = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
        targets_df_dashboard = load_csv('targets.csv', default_columns=[
            '연도', '월', '목표매출', '목표원가율', '목표인건비율',
            '목표임대료율', '목표기타비용율', '목표순이익률'
        ])
        
        # 매출과 방문자 데이터 통합 (캐시된 함수 사용, version_token 기반)
        store_id = _get_current_store_id() or "default"
        v_sales = get_data_version("sales")
        v_visitors = get_data_version("visitors")
        
        # 날짜 범위 설정 (전체 데이터 사용)
        start_date = dt.date(2020, 1, 1)  # 충분히 이른 날짜
        end_date = today_kst()
        
        t0 = time.perf_counter()
        merged_df_dashboard = compute_merged_sales_visitors(store_id, start_date, end_date, v_sales, v_visitors)
        t1 = time.perf_counter()
        record_compute_call("dashboard: merge_sales_visitors", (t1 - t0) * 1000, 
                          rows_in=len(sales_df_dashboard) + len(visitors_df_dashboard), 
                          rows_out=len(merged_df_dashboard), note="cached_token")
        
        # 날짜 컬럼을 datetime으로 변환
        if not merged_df_dashboard.empty and '날짜' in merged_df_dashboard.columns:
            merged_df_dashboard['날짜'] = pd.to_datetime(merged_df_dashboard['날짜'])
        
        # 이번달 데이터 필터링
        month_data_dashboard = merged_df_dashboard[
            (merged_df_dashboard['날짜'].dt.year == current_year) & 
            (merged_df_dashboard['날짜'].dt.month == current_month)
        ].copy() if not merged_df_dashboard.empty else pd.DataFrame()
        
        month_total_sales_dashboard = month_data_dashboard['총매출'].sum() if not month_data_dashboard.empty and '총매출' in month_data_dashboard.columns else 0
        month_total_visitors_dashboard = month_data_dashboard['방문자수'].sum() if not month_data_dashboard.empty and '방문자수' in month_data_dashboard.columns else 0
        
        # 목표 매출 확인
        target_sales_dashboard = 0
        target_row_dashboard = targets_df_dashboard[
            (targets_df_dashboard['연도'] == current_year) & 
            (targets_df_dashboard['월'] == current_month)
        ]
        if not target_row_dashboard.empty:
            target_sales_dashboard = float(safe_get_value(target_row_dashboard, '목표매출', 0))
        
        if not merged_df_dashboard.empty:
            # 1. 이번달 요약
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📊 이번달 요약
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            if not month_data_dashboard.empty:
                month_avg_daily_sales = month_total_sales_dashboard / len(month_data_dashboard) if len(month_data_dashboard) > 0 else 0
                month_avg_daily_visitors = month_total_visitors_dashboard / len(month_data_dashboard) if len(month_data_dashboard) > 0 else 0
                avg_customer_value = month_total_sales_dashboard / month_total_visitors_dashboard if month_total_visitors_dashboard > 0 else 0
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("이번달 누적 매출", f"{month_total_sales_dashboard:,.0f}원")
                with col2:
                    st.metric("평균 일일 매출", f"{month_avg_daily_sales:,.0f}원")
                with col3:
                    st.metric("이번달 총 방문자", f"{int(month_total_visitors_dashboard):,}명")
                with col4:
                    st.metric("평균 객단가", f"{avg_customer_value:,.0f}원")
                with col5:
                    # 목표 달성률 계산
                    target_achievement = (month_total_sales_dashboard / target_sales_dashboard * 100) if target_sales_dashboard > 0 else None
                    if target_achievement is not None:
                        st.metric("목표 달성률", f"{target_achievement:.1f}%", 
                                f"{target_achievement - 100:.1f}%p" if target_achievement != 100 else "0%p")
                    else:
                        st.metric("목표 달성률", "-", help="목표 매출이 설정되지 않았습니다")
            
            st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
            
            # 2. 저장된 매출 내역
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📋 저장된 매출 내역
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            if not merged_df_dashboard.empty:
                # 통합 데이터 표시
                display_df_dashboard = merged_df_dashboard.copy()
                
                # 표시할 컬럼만 선택
                display_columns = []
                if '날짜' in display_df_dashboard.columns:
                    display_columns.append('날짜')
                if '매장' in display_df_dashboard.columns:
                    display_columns.append('매장')
                if '카드매출' in display_df_dashboard.columns:
                    display_columns.append('카드매출')
                if '현금매출' in display_df_dashboard.columns:
                    display_columns.append('현금매출')
                if '총매출' in display_df_dashboard.columns:
                    display_columns.append('총매출')
                if '방문자수' in display_df_dashboard.columns:
                    display_columns.append('방문자수')
                
                # 필요한 컬럼만 선택
                if display_columns:
                    display_df_dashboard = display_df_dashboard[display_columns]
                    
                    # 날짜를 문자열로 변환
                    if '날짜' in display_df_dashboard.columns:
                        display_df_dashboard['날짜'] = pd.to_datetime(display_df_dashboard['날짜']).dt.strftime('%Y-%m-%d')
                    
                    # 숫자 포맷팅
                    if '총매출' in display_df_dashboard.columns:
                        display_df_dashboard['총매출'] = display_df_dashboard['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '카드매출' in display_df_dashboard.columns:
                        display_df_dashboard['카드매출'] = display_df_dashboard['카드매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '현금매출' in display_df_dashboard.columns:
                        display_df_dashboard['현금매출'] = display_df_dashboard['현금매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '방문자수' in display_df_dashboard.columns:
                        display_df_dashboard['방문자수'] = display_df_dashboard['방문자수'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
                
                # AgGrid로 렌더링 (다크 테마 적용 가능, 패키지 없으면 자동 fallback)
                render_aggrid(
                    display_df_dashboard,
                    key="dashboard_daily_table",
                    height=300,
                    sortable=True,
                    filterable=True,
                    resizable=True
                )
            
            st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
            
            # 3. 월별 요약 (최근 6개월)
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📋 월별 요약 (최근 6개월)
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # 최근 6개월 데이터 (캐시된 함수 사용, version_token 기반)
            today_dashboard = today_kst()
            six_months_ago = today_dashboard - timedelta(days=180)
            store_id = _get_current_store_id() or "default"
            v_sales = get_data_version("sales")
            v_visitors = get_data_version("visitors")
            
            t0 = time.perf_counter()
            monthly_summary = compute_monthly_summary(store_id, six_months_ago, today_dashboard, v_sales, v_visitors)
            t1 = time.perf_counter()
            if not monthly_summary.empty:
                record_compute_call("dashboard: monthly_summary_groupby", (t1 - t0) * 1000,
                                  rows_in=len(merged_df_dashboard), rows_out=len(monthly_summary), note="cached_token")
            
            if not monthly_summary.empty:
                
                display_monthly = monthly_summary.head(6).copy()
                display_monthly['월'] = display_monthly['월'].apply(lambda x: f"{int(x)}월")
                display_monthly['월총매출'] = display_monthly['월총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                display_monthly['일평균매출'] = display_monthly['일평균매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                display_monthly['월총방문자'] = display_monthly['월총방문자'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
                display_monthly['월별객단가'] = display_monthly['월별객단가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                display_monthly['전월대비'] = display_monthly['전월대비'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
                
                # AgGrid로 렌더링 (다크 테마 적용 가능, 패키지 없으면 자동 fallback)
                render_aggrid(
                    display_monthly[['연도', '월', '영업일수', '월총매출', '일평균매출', '월총방문자', '월별객단가', '전월대비']],
                    key="dashboard_monthly_table",
                    height=350,
                    sortable=True,
                    filterable=True,
                    resizable=True
                )
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # ========== 판매 ABC 분석 ==========
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📊 판매 ABC 분석
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # ABC 분석 자동 실행
        # 판매 데이터 로드
        menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
        daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
        
        if not daily_sales_df.empty and not menu_df.empty:
            # 날짜 변환
            daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
            
            # 이번 달 데이터 필터링 (KST 기준)
            start_of_month = dt.date(current_year, current_month, 1)
            # 월의 마지막 날 계산
            if current_month < 12:
                next_month_first = dt.date(current_year, current_month + 1, 1)
                days_in_month = (next_month_first - timedelta(days=1)).day
            else:
                days_in_month = 31
            end_of_month = dt.date(current_year, current_month, days_in_month)
            
            filtered_sales_df = daily_sales_df[
                (daily_sales_df['날짜'].dt.date >= start_of_month) & 
                (daily_sales_df['날짜'].dt.date <= end_of_month)
            ].copy()
            
            if not filtered_sales_df.empty:
                # 메뉴별 판매 집계 및 조인 (캐시된 함수 사용, version_token 기반)
                store_id = _get_current_store_id() or "default"
                v_sales = get_data_version("sales")
                v_menus = get_data_version("menus")
                v_cost = get_data_version("cost")
                
                t0 = time.perf_counter()
                summary_df = compute_menu_sales_summary(store_id, start_of_month, end_of_month, v_sales, v_menus, v_cost)
                t1 = time.perf_counter()
                record_compute_call("dashboard: menu_sales_summary", (t1 - t0) * 1000,
                                  rows_in=len(filtered_sales_df), rows_out=len(summary_df), note="cached_token")
                
                # 총 매출 계산
                total_revenue = summary_df['매출'].sum()
                
                if total_revenue > 0:
                    # ABC 분석
                    summary_df = summary_df.sort_values('매출', ascending=False)
                    summary_df['비율(%)'] = (summary_df['매출'] / total_revenue * 100).round(2)
                    summary_df['누계 비율(%)'] = summary_df['비율(%)'].cumsum().round(2)
                    
                    # ABC 등급 부여
                    def assign_abc_grade(cumulative_ratio):
                        if cumulative_ratio <= 70:
                            return 'A'
                        elif cumulative_ratio <= 90:
                            return 'B'
                        else:
                            return 'C'
                    
                    t0 = time.perf_counter()
                    summary_df['ABC 등급'] = summary_df['누계 비율(%)'].apply(assign_abc_grade)
                    t1 = time.perf_counter()
                    record_compute_call("dashboard: abc_grade_apply", (t1 - t0) * 1000,
                                      rows_in=len(summary_df), rows_out=len(summary_df))
                    
                    # ABC 등급별 통계
                    t0 = time.perf_counter()
                    abc_stats = summary_df.groupby('ABC 등급').agg({
                        '메뉴명': 'count',
                        '매출': 'sum',
                        '판매수량': 'sum'
                    }).reset_index()
                    t1 = time.perf_counter()
                    record_compute_call("dashboard: abc_stats_groupby", (t1 - t0) * 1000,
                                      rows_in=len(summary_df), rows_out=len(abc_stats))
                    abc_stats.columns = ['ABC 등급', '메뉴 수', '총 매출', '총 판매수량']
                    abc_stats['매출 비율(%)'] = (abc_stats['총 매출'] / total_revenue * 100).round(2)
                    
                    # ABC 등급별 통계 카드
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        a_count = abc_stats[abc_stats['ABC 등급'] == 'A']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                        a_revenue = abc_stats[abc_stats['ABC 등급'] == 'A']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                        a_ratio = abc_stats[abc_stats['ABC 등급'] == 'A']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                            <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟢 A등급</div>
                            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(a_count)}개 메뉴</div>
                            <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(a_revenue):,}원</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {a_ratio:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        b_count = abc_stats[abc_stats['ABC 등급'] == 'B']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                        b_revenue = abc_stats[abc_stats['ABC 등급'] == 'B']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                        b_ratio = abc_stats[abc_stats['ABC 등급'] == 'B']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                            <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟡 B등급</div>
                            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(b_count)}개 메뉴</div>
                            <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(b_revenue):,}원</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {b_ratio:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        c_count = abc_stats[abc_stats['ABC 등급'] == 'C']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                        c_revenue = abc_stats[abc_stats['ABC 등급'] == 'C']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                        c_ratio = abc_stats[abc_stats['ABC 등급'] == 'C']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                            <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🔴 C등급</div>
                            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(c_count)}개 메뉴</div>
                            <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(c_revenue):,}원</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {c_ratio:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # TOP 10 메뉴 표시
                    st.markdown("""
                    <div style="margin: 1rem 0 0.5rem 0;">
                        <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                            🏆 ABC 분석 TOP 10 메뉴
                        </h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    top10_df = summary_df.head(10).copy()
                    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
                    
                    # 표시용 포맷팅
                    display_top10 = top10_df.copy()
                    display_top10['판매수량'] = display_top10['판매수량'].apply(lambda x: f"{int(x):,}개")
                    display_top10['매출'] = display_top10['매출'].apply(lambda x: f"{int(x):,}원")
                    display_top10['비율(%)'] = display_top10['비율(%)'].apply(lambda x: f"{x:.2f}%")
                    display_top10['누계 비율(%)'] = display_top10['누계 비율(%)'].apply(lambda x: f"{x:.2f}%")
                    
                    st.dataframe(
                    display_top10[['순위', '메뉴명', '판매수량', '매출', '비율(%)', '누계 비율(%)', 'ABC 등급']],
                    use_container_width=True,
                    hide_index=True
                    )
                    
                    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                    
                    # ========== 재료 사용량 TOP 10 ==========
                    # 재료 사용량 계산
                    usage_df = calculate_ingredient_usage(filtered_sales_df, recipe_df)
                    
                    if not usage_df.empty and not ingredient_df.empty:
                        # 재료 단가와 조인하여 총 사용 단가 계산
                        usage_df = pd.merge(
                            usage_df,
                            ingredient_df[['재료명', '단가']],
                            on='재료명',
                            how='left'
                        )
                        usage_df['단가'] = usage_df['단가'].fillna(0)
                        usage_df['총사용단가'] = usage_df['총사용량'] * usage_df['단가']
                        
                        # 재료별 총 사용량/총 사용 단가 집계
                        t0 = time.perf_counter()
                        ingredient_summary = (
                            usage_df
                            .groupby('재료명')[['총사용량', '총사용단가']]
                            .sum()
                            .reset_index()
                        )
                        t1 = time.perf_counter()
                        record_compute_call("dashboard: ingredient_summary_groupby", (t1 - t0) * 1000,
                                          rows_in=len(usage_df), rows_out=len(ingredient_summary))
                        
                        # 사용 단가 기준으로 정렬
                        ingredient_summary = ingredient_summary.sort_values('총사용단가', ascending=False)
                        
                        # 총 사용단가 합계 계산
                        total_cost = ingredient_summary['총사용단가'].sum()
                        
                        if total_cost > 0:
                            # 비율 및 누적 비율 계산
                            ingredient_summary['비율(%)'] = (ingredient_summary['총사용단가'] / total_cost * 100).round(2)
                            ingredient_summary['누적 비율(%)'] = ingredient_summary['비율(%)'].cumsum().round(2)
                            
                            # ABC 등급 부여
                            def assign_abc_grade_ingredient(cumulative_ratio):
                                if cumulative_ratio <= 70:
                                    return 'A'
                                elif cumulative_ratio <= 90:
                                    return 'B'
                                else:
                                    return 'C'
                            
                            ingredient_summary['ABC 등급'] = ingredient_summary['누적 비율(%)'].apply(assign_abc_grade_ingredient)
                            
                            st.markdown("""
                            <div style="margin: 1rem 0 0.5rem 0;">
                                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                                    📦 재료 사용 단가 TOP 10
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # TOP 10 재료
                            top10_ingredients = ingredient_summary.head(10).copy()
                            top10_ingredients.insert(0, '순위', range(1, len(top10_ingredients) + 1))
                            
                            # 표시용 포맷팅
                            display_top10_ingredients = top10_ingredients.copy()
                            display_top10_ingredients['총 사용량'] = display_top10_ingredients['총사용량'].apply(lambda x: f"{x:,.2f}")
                            display_top10_ingredients['총 사용단가'] = display_top10_ingredients['총사용단가'].apply(lambda x: f"{int(x):,}원")
                            display_top10_ingredients['비율(%)'] = display_top10_ingredients['비율(%)'].apply(lambda x: f"{x:.2f}%")
                            display_top10_ingredients['누적 비율(%)'] = display_top10_ingredients['누적 비율(%)'].apply(lambda x: f"{x:.2f}%")
                            
                            st.dataframe(
                                display_top10_ingredients[['순위', '재료명', '총 사용량', '총 사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']],
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # TOP 10 총합계
                            top10_total = top10_ingredients['총사용단가'].sum()
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-top: 0.75rem;">
                                <span style="color: #ffffff; font-size: 0.9rem; font-weight: 600;">
                                    💰 TOP 10 총 사용단가 합계: {int(top10_total):,}원
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                    
                    # ========== 레시피 검색 및 수정 ==========
                    recipe_df_dashboard = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
                    
                    if not recipe_df_dashboard.empty:
                        # 레시피가 있는 메뉴 목록 추출
                        menus_with_recipes = recipe_df_dashboard['메뉴명'].unique().tolist()
                        
                        if menus_with_recipes:
                            st.markdown("""
                            <div style="margin: 1rem 0 0.5rem 0;">
                                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                                    🔍 레시피 검색 및 수정
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 메뉴 선택
                            filter_menu = st.selectbox(
                                "메뉴 선택",
                                options=menus_with_recipes,
                                key="dashboard_recipe_filter_menu",
                                index=0 if menus_with_recipes else None
                            )
                            
                            # 선택한 메뉴의 레시피만 필터링
                            display_recipe_df = recipe_df_dashboard[recipe_df_dashboard['메뉴명'] == filter_menu].copy()
                            
                            if not display_recipe_df.empty:
                                # 재료 정보와 조인하여 단위 및 단가 표시
                                display_recipe_df = pd.merge(
                                    display_recipe_df,
                                    ingredient_df[['재료명', '단위', '단가']],
                                    on='재료명',
                                    how='left'
                                )
                                
                                # 원가 계산
                                menu_cost_df = calculate_menu_cost(menu_df, recipe_df_dashboard, ingredient_df)
                                menu_cost_info = menu_cost_df[menu_cost_df['메뉴명'] == filter_menu]
                                
                                # 메뉴 정보 가져오기
                                menu_info = menu_df[menu_df['메뉴명'] == filter_menu]
                                # Phase 1: 안전한 DataFrame 접근
                                menu_price = int(safe_get_value(menu_info, '판매가', 0)) if not menu_info.empty else 0
                                
                                # 조리방법 가져오기 (menu_master에서)
                                cooking_method_text = ""
                                try:
                                    from src.auth import get_supabase_client
                                    supabase = get_supabase_client()
                                    store_id = _get_current_store_id()
                                    if supabase and store_id:
                                        menu_result = supabase.table("menu_master").select("cooking_method").eq("store_id", store_id).eq("name", filter_menu).execute()
                                        if menu_result.data and menu_result.data[0].get('cooking_method'):
                                            cooking_method_text = menu_result.data[0]['cooking_method']
                                except Exception as e:
                                    import logging
                                    logging.getLogger(__name__).warning(f"조리방법 조회 실패 (대시보드): {e}")
                                
                                # 원가 정보
                                cost = int(safe_get_value(menu_cost_info, '원가', 0)) if not menu_cost_info.empty else 0
                                cost_rate = float(safe_get_value(menu_cost_info, '원가율', 0)) if not menu_cost_info.empty else 0
                                
                                # 메뉴 정보 카드
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                        <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">판매가</div>
                                        <div style="font-size: 1.3rem; font-weight: 700;">{menu_price:,}원</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                        <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가</div>
                                        <div style="font-size: 1.3rem; font-weight: 700;">{cost:,}원</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col3:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                        <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가율</div>
                                        <div style="font-size: 1.3rem; font-weight: 700;">{cost_rate:.1f}%</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # 구성 재료 및 사용량 테이블
                                st.markdown("""
                                <div style="margin: 1rem 0 0.5rem 0;">
                                    <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                                        📋 구성 재료 및 사용량
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # 테이블 데이터 준비
                                table_data = []
                                for idx, row in display_recipe_df.iterrows():
                                    ing_name = row['재료명']
                                    unit = row['단위'] if pd.notna(row['단위']) else ""
                                    current_qty = float(row['사용량'])
                                    unit_price = float(row['단가']) if pd.notna(row['단가']) else 0
                                    ingredient_cost = current_qty * unit_price
                                    
                                    table_data.append({
                                        '재료명': ing_name,
                                        '기준단위': unit,
                                        '사용량': f"{current_qty:.2f}",
                                        '1단위 단가': f"{unit_price:,.1f}원",
                                        '재료비': f"{ingredient_cost:,.1f}원"
                                    })
                                
                                # 테이블 표시
                                ingredients_table_df = pd.DataFrame(table_data)
                                st.dataframe(ingredients_table_df, use_container_width=True, hide_index=True)
                                
                                # 조리방법 표시
                                st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                                st.markdown("""
                                <div style="margin: 1rem 0 0.5rem 0;">
                                    <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                                        👨‍🍳 조리방법
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if cooking_method_text:
                                    st.markdown(f"""
                                    <div style="background: rgba(30, 41, 59, 0.5); padding: 1rem; border-radius: 12px; 
                                                border-left: 4px solid #667eea; margin: 0.75rem 0;">
                                        <div style="color: #e5e7eb; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap;">
                                            {cooking_method_text.replace(chr(10), '<br>')}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.info("조리방법이 등록되지 않았습니다.")
                    
    else:
        st.info("손익분기 매출을 계산하려면 목표 비용구조 페이지에서 고정비와 변동비율을 입력해주세요.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_dashboard()
