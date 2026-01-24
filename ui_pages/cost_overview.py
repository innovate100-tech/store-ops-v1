"""
원가 분석 페이지 (고도화)
ZONE A~I: 핵심 지표, 메뉴별 원가 분석, 판매 데이터 연계, ABC 분석, 시뮬레이션, 트렌드, 목표 vs 실제, 액션 제안
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.ui_helpers import render_page_header, render_section_header, render_section_divider
from src.storage_supabase import load_csv
from src.analytics import calculate_menu_cost, abc_analysis
from src.auth import get_current_store_id
from src.utils.time_utils import current_year_kst, current_month_kst

bootstrap(page_title="원가 분석")


def _get_menu_ingredient_cost(menu_name: str, recipe_df: pd.DataFrame, ingredient_df: pd.DataFrame) -> pd.DataFrame:
    """메뉴별 재료별 원가 구성 계산"""
    menu_recipes = recipe_df[recipe_df['메뉴명'] == menu_name].copy()
    if menu_recipes.empty:
        return pd.DataFrame(columns=['재료명', '사용량', '단가', '원가', '원가비중(%)'])
    
    merged = pd.merge(menu_recipes, ingredient_df[['재료명', '단가']], on='재료명', how='left')
    merged['단가'] = merged['단가'].fillna(0)
    merged['원가'] = merged['사용량'] * merged['단가']
    total_cost = merged['원가'].sum()
    merged['원가비중(%)'] = (merged['원가'] / total_cost * 100).round(2) if total_cost > 0 else 0.0
    merged = merged.sort_values('원가', ascending=False)
    return merged[['재료명', '사용량', '단가', '원가', '원가비중(%)']]


def _calculate_cost_contribution(cost_df: pd.DataFrame, daily_sales_df: pd.DataFrame, period_days: int = 30) -> pd.DataFrame:
    """원가 기여도 계산 (판매량 × 원가)"""
    if cost_df.empty or daily_sales_df.empty:
        return pd.DataFrame(columns=['메뉴명', '판매량', '원가', '총원가기여도', '순위'])
    
    # 컬럼명 정규화
    filtered = daily_sales_df.copy()
    if 'date' in filtered.columns:
        filtered['날짜'] = pd.to_datetime(filtered['date'])
    elif '날짜' in filtered.columns:
        filtered['날짜'] = pd.to_datetime(filtered['날짜'])
    
    if 'menu_name' in filtered.columns:
        filtered['메뉴명'] = filtered['menu_name']
    elif '메뉴명' not in filtered.columns:
        return pd.DataFrame(columns=['메뉴명', '판매량', '원가', '총원가기여도', '순위'])
    
    if 'quantity' in filtered.columns:
        filtered['판매수량'] = filtered['quantity']
    elif '판매수량' not in filtered.columns:
        return pd.DataFrame(columns=['메뉴명', '판매량', '원가', '총원가기여도', '순위'])
    
    # 기간 필터링
    if '날짜' in filtered.columns:
        cutoff = datetime.now() - timedelta(days=period_days)
        filtered = filtered[filtered['날짜'] >= cutoff].copy()
    
    if filtered.empty:
        return pd.DataFrame(columns=['메뉴명', '판매량', '원가', '총원가기여도', '순위'])
    
    # 메뉴별 판매량 집계
    sales_summary = filtered.groupby('메뉴명')['판매수량'].sum().reset_index()
    sales_summary.columns = ['메뉴명', '판매량']
    
    # 원가 정보와 조인
    result = pd.merge(sales_summary, cost_df[['메뉴명', '원가']], on='메뉴명', how='left')
    result['원가'] = result['원가'].fillna(0)
    result['총원가기여도'] = result['판매량'] * result['원가']
    result = result.sort_values('총원가기여도', ascending=False)
    result['순위'] = range(1, len(result) + 1)
    return result[['메뉴명', '판매량', '원가', '총원가기여도', '순위']]


def _calculate_contribution_margin(cost_df: pd.DataFrame, daily_sales_df: pd.DataFrame, period_days: int = 30) -> pd.DataFrame:
    """공헌이익 계산 ((판매가 - 원가) × 판매량)"""
    if cost_df.empty or daily_sales_df.empty:
        return pd.DataFrame(columns=['메뉴명', '판매량', '매출', '원가', '공헌이익', '공헌이익률(%)'])
    
    # 컬럼명 정규화
    filtered = daily_sales_df.copy()
    if 'date' in filtered.columns:
        filtered['날짜'] = pd.to_datetime(filtered['date'])
    elif '날짜' in filtered.columns:
        filtered['날짜'] = pd.to_datetime(filtered['날짜'])
    
    if 'menu_name' in filtered.columns:
        filtered['메뉴명'] = filtered['menu_name']
    elif '메뉴명' not in filtered.columns:
        return pd.DataFrame(columns=['메뉴명', '판매량', '매출', '원가', '공헌이익', '공헌이익률(%)'])
    
    if 'quantity' in filtered.columns:
        filtered['판매수량'] = filtered['quantity']
    elif '판매수량' not in filtered.columns:
        return pd.DataFrame(columns=['메뉴명', '판매량', '매출', '원가', '공헌이익', '공헌이익률(%)'])
    
    # 기간 필터링
    if '날짜' in filtered.columns:
        cutoff = datetime.now() - timedelta(days=period_days)
        filtered = filtered[filtered['날짜'] >= cutoff].copy()
    
    if filtered.empty:
        return pd.DataFrame(columns=['메뉴명', '판매량', '매출', '원가', '공헌이익', '공헌이익률(%)'])
    
    # 메뉴별 판매량 집계
    sales_summary = filtered.groupby('메뉴명')['판매수량'].sum().reset_index()
    sales_summary.columns = ['메뉴명', '판매량']
    
    # 원가 정보와 조인
    result = pd.merge(sales_summary, cost_df[['메뉴명', '판매가', '원가']], on='메뉴명', how='left')
    result['판매가'] = result['판매가'].fillna(0)
    result['원가'] = result['원가'].fillna(0)
    result['매출'] = result['판매량'] * result['판매가']
    result['공헌이익'] = (result['판매가'] - result['원가']) * result['판매량']
    result['공헌이익률(%)'] = (result['공헌이익'] / result['매출'] * 100).round(2) if (result['매출'] > 0).any() else 0.0
    result = result.sort_values('공헌이익', ascending=False)
    return result[['메뉴명', '판매량', '매출', '원가', '공헌이익', '공헌이익률(%)']]


def _abc_analysis_by_cost_rate(cost_df: pd.DataFrame) -> pd.DataFrame:
    """원가율 기준 ABC 분석"""
    if cost_df.empty:
        return pd.DataFrame(columns=['메뉴명', '원가율', 'ABC등급'])
    
    result = cost_df[['메뉴명', '원가율']].copy()
    result['ABC등급'] = result['원가율'].apply(
        lambda x: 'A' if x >= 35 else ('B' if x >= 30 else 'C')
    )
    return result.sort_values('원가율', ascending=False)


def _simulate_cost_change(menu_name: str, ingredient_name: str, price_change_pct: float,
                          recipe_df: pd.DataFrame, ingredient_df: pd.DataFrame, menu_df: pd.DataFrame) -> dict:
    """재료 단가 변경 시뮬레이션"""
    menu_recipes = recipe_df[recipe_df['메뉴명'] == menu_name].copy()
    if menu_recipes.empty:
        return {}
    
    ingredient_row = menu_recipes[menu_recipes['재료명'] == ingredient_name]
    if ingredient_row.empty:
        return {}
    
    # 현재 원가 계산
    current_cost = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
    current_menu = current_cost[current_cost['메뉴명'] == menu_name]
    if current_menu.empty:
        return {}
    
    current_cost_val = float(current_menu.iloc[0]['원가'])
    current_rate = float(current_menu.iloc[0]['원가율'])
    current_price = float(current_menu.iloc[0]['판매가'])
    
    # 변경 후 재료 단가
    current_ingredient_price = float(ingredient_df[ingredient_df['재료명'] == ingredient_name].iloc[0]['단가'])
    new_ingredient_price = current_ingredient_price * (1 + price_change_pct / 100)
    
    # 변경 후 재료 마스터
    new_ingredient_df = ingredient_df.copy()
    new_ingredient_df.loc[new_ingredient_df['재료명'] == ingredient_name, '단가'] = new_ingredient_price
    
    # 변경 후 원가 계산
    new_cost = calculate_menu_cost(menu_df, recipe_df, new_ingredient_df)
    new_menu = new_cost[new_cost['메뉴명'] == menu_name]
    if new_menu.empty:
        return {}
    
    new_cost_val = float(new_menu.iloc[0]['원가'])
    new_rate = float(new_menu.iloc[0]['원가율'])
    
    return {
        'menu_name': menu_name,
        'ingredient_name': ingredient_name,
        'price_change_pct': price_change_pct,
        'current_cost': current_cost_val,
        'current_rate': current_rate,
        'new_cost': new_cost_val,
        'new_rate': new_rate,
        'cost_change': new_cost_val - current_cost_val,
        'rate_change': new_rate - current_rate,
    }


def _simulate_usage_change(menu_name: str, ingredient_name: str, usage_change_pct: float,
                          recipe_df: pd.DataFrame, ingredient_df: pd.DataFrame, menu_df: pd.DataFrame) -> dict:
    """재료 사용량 변경 시뮬레이션"""
    menu_recipes = recipe_df[recipe_df['메뉴명'] == menu_name].copy()
    if menu_recipes.empty:
        return {}
    
    ingredient_row = menu_recipes[menu_recipes['재료명'] == ingredient_name]
    if ingredient_row.empty:
        return {}
    
    # 현재 원가 계산
    current_cost = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
    current_menu = current_cost[current_cost['메뉴명'] == menu_name]
    if current_menu.empty:
        return {}
    
    current_cost_val = float(current_menu.iloc[0]['원가'])
    current_rate = float(current_menu.iloc[0]['원가율'])
    
    # 변경 후 사용량
    current_usage = float(ingredient_row.iloc[0]['사용량'])
    new_usage = current_usage * (1 + usage_change_pct / 100)
    
    # 변경 후 레시피
    new_recipe_df = recipe_df.copy()
    mask = (new_recipe_df['메뉴명'] == menu_name) & (new_recipe_df['재료명'] == ingredient_name)
    new_recipe_df.loc[mask, '사용량'] = new_usage
    
    # 변경 후 원가 계산
    new_cost = calculate_menu_cost(menu_df, new_recipe_df, ingredient_df)
    new_menu = new_cost[new_cost['메뉴명'] == menu_name]
    if new_menu.empty:
        return {}
    
    new_cost_val = float(new_menu.iloc[0]['원가'])
    new_rate = float(new_menu.iloc[0]['원가율'])
    
    return {
        'menu_name': menu_name,
        'ingredient_name': ingredient_name,
        'usage_change_pct': usage_change_pct,
        'current_cost': current_cost_val,
        'current_rate': current_rate,
        'new_cost': new_cost_val,
        'new_rate': new_rate,
        'cost_change': new_cost_val - current_cost_val,
        'rate_change': new_rate - current_rate,
    }


def _detect_ingredient_price_increase(ingredient_df: pd.DataFrame, months: int = 3) -> pd.DataFrame:
    """재료 단가 상승 감지 (현재는 단가 이력이 없으므로 현재 단가만 반환)"""
    # 단가 이력이 없으면 현재 단가만 표시
    result = ingredient_df[['재료명', '단가']].copy()
    result['변화율(%)'] = 0.0  # 이력 없으면 변화율 0
    result['영향메뉴수'] = 0  # 추후 계산 가능
    return result.sort_values('단가', ascending=False)


def _render_zone_a(cost_df: pd.DataFrame, cost_contribution_df: pd.DataFrame = None):
    """ZONE A: 핵심 지표"""
    render_section_header("핵심 지표", "📊")
    
    if cost_df.empty:
        st.info("원가를 계산하려면 메뉴, 레시피, 재료 데이터가 모두 필요합니다.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_rate = cost_df['원가율'].mean()
        st.metric("평균 원가율", f"{avg_rate:.2f}%")
    with col2:
        max_rate = cost_df['원가율'].max()
        st.metric("최고 원가율", f"{max_rate:.2f}%")
    with col3:
        min_rate = cost_df['원가율'].min()
        st.metric("최저 원가율", f"{min_rate:.2f}%")
    with col4:
        high_cost_count = len(cost_df[cost_df['원가율'] >= 35])
        st.metric("고원가율 메뉴 수", f"{high_cost_count}개", delta="35% 이상" if high_cost_count > 0 else None)
    
    if cost_contribution_df is not None and not cost_contribution_df.empty:
        total_contribution = cost_contribution_df['총원가기여도'].sum()
        st.caption(f"💰 총 원가 기여도: **{int(total_contribution):,}원** (판매량 × 원가 합계)")


def _render_zone_b(cost_df: pd.DataFrame, recipe_df: pd.DataFrame, ingredient_df: pd.DataFrame):
    """ZONE B: 메뉴별 원가 분석 (기존 강화)"""
    render_section_header("메뉴별 원가 분석", "📋")
    
    if cost_df.empty:
        st.info("원가를 계산할 데이터가 없습니다.")
        return
    
    # 원가율 경고 표시
    high_cost_count = len(cost_df[cost_df['원가율'] >= 35])
    if high_cost_count > 0:
        st.warning(f"⚠️ 원가율이 35% 이상인 메뉴가 {high_cost_count}개 있습니다. 수익성을 검토해주세요.")
    
    # 메뉴별 원가/원가율 테이블
    display_df = cost_df.copy()
    display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
    display_df['원가'] = display_df['원가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
    display_df['원가율'] = display_df['원가율'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    
    st.dataframe(display_df[['메뉴명', '판매가', '원가', '원가율']], use_container_width=True, hide_index=True)
    
    # 메뉴 선택 시 재료별 원가 구성
    if not cost_df.empty:
        selected_menu = st.selectbox("메뉴 선택 (재료별 원가 구성 보기)", cost_df['메뉴명'].tolist(), key="cost_menu_select")
        if selected_menu:
            ingredient_cost = _get_menu_ingredient_cost(selected_menu, recipe_df, ingredient_df)
            if not ingredient_cost.empty:
                st.markdown(f"**{selected_menu} 재료별 원가 구성**")
                st.bar_chart(ingredient_cost.set_index('재료명')['원가'], height=250)
                st.dataframe(ingredient_cost, use_container_width=True, hide_index=True)
                
                # 재료 단가 시뮬레이션
                with st.expander("재료 단가 시뮬레이션"):
                    selected_ingredient = st.selectbox("재료 선택", ingredient_cost['재료명'].tolist(), key="sim_ingredient")
                    change_pct = st.slider("단가 변화율 (%)", -20, 20, 0, 1)
                    if st.button("시뮬레이션 실행", key="sim_cost_change"):
                        sim_result = _simulate_cost_change(selected_menu, selected_ingredient, change_pct, recipe_df, ingredient_df, cost_df)
                        if sim_result:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("현재 원가율", f"{sim_result['current_rate']:.2f}%")
                            with col2:
                                st.metric("변경 후 원가율", f"{sim_result['new_rate']:.2f}%", 
                                         delta=f"{sim_result['rate_change']:+.2f}%p")


def _render_zone_c(cost_df: pd.DataFrame, daily_sales_df: pd.DataFrame):
    """ZONE C: 판매 데이터 연계 분석"""
    render_section_header("판매 데이터 연계 분석", "📊")
    
    if daily_sales_df.empty:
        st.info("판매 데이터가 없으면 원가 기여도와 공헌이익을 분석할 수 없습니다. **판매 관리** 페이지에서 판매량을 입력하세요.")
        return
    
    period = st.radio("기간 선택", [30, 90, 180], format_func=lambda x: f"최근 {x}일", horizontal=True, key="cost_period")
    
    cost_contribution = _calculate_cost_contribution(cost_df, daily_sales_df, period)
    contribution_margin = _calculate_contribution_margin(cost_df, daily_sales_df, period)
    
    if not cost_contribution.empty:
        st.markdown("**원가 기여도 TOP 10**")
        top10 = cost_contribution.head(10)
        st.bar_chart(top10.set_index('메뉴명')['총원가기여도'], height=250)
        st.dataframe(top10, use_container_width=True, hide_index=True)
    
    if not contribution_margin.empty:
        st.markdown("**공헌이익 TOP 10**")
        top10_margin = contribution_margin.head(10)
        st.bar_chart(top10_margin.set_index('메뉴명')['공헌이익'], height=250)
        st.dataframe(top10_margin, use_container_width=True, hide_index=True)
        
        # 원가율 구간별 매출 분포
        cost_df_with_sales = pd.merge(cost_df, contribution_margin[['메뉴명', '매출']], on='메뉴명', how='left')
        cost_df_with_sales['매출'] = cost_df_with_sales['매출'].fillna(0)
        cost_df_with_sales['원가율구간'] = cost_df_with_sales['원가율'].apply(
            lambda x: '30% 미만' if x < 30 else ('30-35%' if x < 35 else '35% 이상')
        )
        sales_by_segment = cost_df_with_sales.groupby('원가율구간')['매출'].sum()
        if not sales_by_segment.empty:
            st.markdown("**원가율 구간별 매출 분포**")
                    st.bar_chart(sales_by_segment)


def _render_zone_d(cost_df: pd.DataFrame, daily_sales_df: pd.DataFrame):
    """ZONE D: ABC 분석"""
    render_section_header("ABC 분석", "📊")
    
    if cost_df.empty:
        st.info("원가 데이터가 없으면 ABC 분석을 할 수 없습니다.")
        return
    
    # 원가율 기준 ABC
    st.markdown("**원가율 기준 ABC 분석**")
    abc_by_rate = _abc_analysis_by_cost_rate(cost_df)
    if not abc_by_rate.empty:
        st.dataframe(abc_by_rate, use_container_width=True, hide_index=True)
        abc_summary = abc_by_rate.groupby('ABC등급').size()
        st.bar_chart(abc_summary)
    
    # 공헌이익 기준 ABC (판매 데이터 있을 때)
    if not daily_sales_df.empty:
        st.markdown("**공헌이익 기준 ABC 분석**")
        period = 30
        contribution_margin = _calculate_contribution_margin(cost_df, daily_sales_df, period)
        if not contribution_margin.empty:
            abc_by_contribution = abc_analysis(daily_sales_df, cost_df[['메뉴명', '판매가']], cost_df)
            if not abc_by_contribution.empty:
                st.dataframe(abc_by_contribution[['메뉴명', '공헌이익', 'ABC등급']], use_container_width=True, hide_index=True)
                
                # 원가율 vs 공헌이익 매트릭스
                merged = pd.merge(cost_df[['메뉴명', '원가율']], contribution_margin[['메뉴명', '공헌이익']], on='메뉴명', how='inner')
                if not merged.empty:
                    st.markdown("**원가율 vs 공헌이익 매트릭스**")
                    # 산점도는 matplotlib 또는 plotly 필요, 일단 테이블로 표시
                    st.dataframe(merged[['메뉴명', '원가율', '공헌이익']].head(20), use_container_width=True, hide_index=True)
                    st.caption("💡 원가율 vs 공헌이익 매트릭스: 좌상(원가율 높음, 공헌이익 높음), 좌하(원가율 높음, 공헌이익 낮음), 우상(원가율 낮음, 공헌이익 높음), 우하(원가율 낮음, 공헌이익 낮음)")


def _render_zone_e(cost_df: pd.DataFrame, recipe_df: pd.DataFrame, ingredient_df: pd.DataFrame):
    """ZONE E: 원가 최적화 시뮬레이션"""
    render_section_header("원가 최적화 시뮬레이션", "🔧")
    
    if cost_df.empty:
        st.info("원가 데이터가 없으면 시뮬레이션을 할 수 없습니다.")
        return
    
    menu_df = cost_df[['메뉴명', '판매가']].copy()
    
    tab1, tab2, tab3 = st.tabs(["재료 단가 변경", "재료 사용량 변경", "목표 원가율 달성"])
    
    with tab1:
        selected_menu = st.selectbox("메뉴 선택", cost_df['메뉴명'].tolist(), key="sim_menu_price")
        if selected_menu:
            menu_recipes = recipe_df[recipe_df['메뉴명'] == selected_menu]
            if not menu_recipes.empty:
                selected_ingredient = st.selectbox("재료 선택", menu_recipes['재료명'].tolist(), key="sim_ingredient_price")
                change_pct = st.slider("단가 변화율 (%)", -20, 20, 0, 1, key="sim_price_pct")
                if st.button("시뮬레이션 실행", key="sim_price_btn"):
                    result = _simulate_cost_change(selected_menu, selected_ingredient, change_pct, recipe_df, ingredient_df, menu_df)
                    if result:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("현재 원가율", f"{result['current_rate']:.2f}%")
                        with col2:
                            st.metric("변경 후 원가율", f"{result['new_rate']:.2f}%", 
                                     delta=f"{result['rate_change']:+.2f}%p")
                        with col3:
                            st.metric("원가 변화", f"{result['cost_change']:+,.0f}원")
    
    with tab2:
        selected_menu2 = st.selectbox("메뉴 선택", cost_df['메뉴명'].tolist(), key="sim_menu_usage")
        if selected_menu2:
            menu_recipes2 = recipe_df[recipe_df['메뉴명'] == selected_menu2]
            if not menu_recipes2.empty:
                selected_ingredient2 = st.selectbox("재료 선택", menu_recipes2['재료명'].tolist(), key="sim_ingredient_usage")
                change_pct2 = st.slider("사용량 변화율 (%)", -20, 20, 0, 1, key="sim_usage_pct")
                st.caption("⚠️ 사용량 감소 시 품질 저하 가능성이 있습니다.")
                if st.button("시뮬레이션 실행", key="sim_usage_btn"):
                    result = _simulate_usage_change(selected_menu2, selected_ingredient2, change_pct2, recipe_df, ingredient_df, menu_df)
                    if result:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("현재 원가율", f"{result['current_rate']:.2f}%")
                        with col2:
                            st.metric("변경 후 원가율", f"{result['new_rate']:.2f}%", 
                                     delta=f"{result['rate_change']:+.2f}%p")
                        with col3:
                            st.metric("원가 변화", f"{result['cost_change']:+,.0f}원")
    
    with tab3:
        selected_menu3 = st.selectbox("메뉴 선택", cost_df['메뉴명'].tolist(), key="sim_menu_target")
        target_rate = st.number_input("목표 원가율 (%)", min_value=0.0, max_value=100.0, value=30.0, step=0.1, key="target_rate")
        if selected_menu3:
            current_menu = cost_df[cost_df['메뉴명'] == selected_menu3]
            if not current_menu.empty:
                current_rate = float(current_menu.iloc[0]['원가율'])
                if current_rate > target_rate:
                    diff = current_rate - target_rate
                    st.info(f"현재 원가율 {current_rate:.2f}%에서 목표 {target_rate:.1f}%까지 {diff:.2f}%p 감소가 필요합니다.")
                    st.caption("💡 재료 단가 재협상 또는 재료 사용량 조정을 고려하세요.")


def _render_zone_f(cost_df: pd.DataFrame, ingredient_df: pd.DataFrame):
    """ZONE F: 원가 트렌드"""
    render_section_header("원가 트렌드", "📈")
    
    if cost_df.empty:
        st.info("원가 데이터가 없으면 트렌드를 분석할 수 없습니다.")
        return
    
    st.markdown("**재료 단가 상승 감지**")
    price_increase = _detect_ingredient_price_increase(ingredient_df, months=3)
    if not price_increase.empty:
        st.dataframe(price_increase[['재료명', '단가', '변화율(%)']], use_container_width=True, hide_index=True)
        st.caption("💡 재료 단가 이력이 없으면 변화율을 계산할 수 없습니다.")
    
    st.markdown("**원가율 변화 추이**")
    st.caption("💡 월별 원가율 추이는 재료 단가 이력이 필요합니다. 현재는 현재 시점 원가율만 표시됩니다.")


def _render_zone_g(cost_df: pd.DataFrame):
    """ZONE G: 목표 vs 실제"""
    render_section_header("목표 vs 실제", "🎯")
    
    if cost_df.empty:
        st.info("원가 데이터가 없으면 목표와 비교할 수 없습니다.")
        return
    
    st.info("💡 목표 원가율 설정 기능은 추후 구현 예정입니다. 현재는 실제 원가율만 표시됩니다.")
    
    # 기본 목표 원가율 30%로 가정
    target_rate = 30.0
    cost_df_with_target = cost_df.copy()
    cost_df_with_target['목표원가율'] = target_rate
    cost_df_with_target['차이(%p)'] = cost_df_with_target['원가율'] - cost_df_with_target['목표원가율']
    cost_df_with_target['달성여부'] = cost_df_with_target['차이(%p)'].apply(lambda x: '달성' if x <= 0 else '미달')
    
    achievement_rate = (len(cost_df_with_target[cost_df_with_target['달성여부'] == '달성']) / len(cost_df_with_target) * 100) if len(cost_df_with_target) > 0 else 0
    st.metric("목표 달성률", f"{achievement_rate:.1f}%", 
             delta=f"목표: {target_rate}%")
    
    st.markdown("**목표 미달 메뉴**")
    under_target = cost_df_with_target[cost_df_with_target['달성여부'] == '미달'].sort_values('차이(%p)', ascending=False)
    if not under_target.empty:
        display = under_target[['메뉴명', '원가율', '목표원가율', '차이(%p)']].copy()
        display['원가율'] = display['원가율'].apply(lambda x: f"{x:.2f}%")
        display['목표원가율'] = display['목표원가율'].apply(lambda x: f"{x:.1f}%")
        display['차이(%p)'] = display['차이(%p)'].apply(lambda x: f"{x:+.2f}%p")
        st.dataframe(display, use_container_width=True, hide_index=True)


def _render_zone_h(cost_df: pd.DataFrame, cost_contribution_df: pd.DataFrame = None):
    """ZONE H: 원가 최적화 액션"""
    render_section_header("원가 최적화 액션", "💡")
    
    if cost_df.empty:
        st.info("원가 데이터가 없으면 액션을 제안할 수 없습니다.")
        return
    
    # 자동 진단
    high_cost_menus = cost_df[cost_df['원가율'] >= 35].sort_values('원가율', ascending=False)
    
    if not high_cost_menus.empty:
        st.markdown("**고원가율 메뉴 (35% 이상)**")
        for idx, row in high_cost_menus.head(5).iterrows():
            st.markdown(f"- **{row['메뉴명']}**: 원가율 {row['원가율']:.2f}%")
            if cost_contribution_df is not None and not cost_contribution_df.empty:
                contrib = cost_contribution_df[cost_contribution_df['메뉴명'] == row['메뉴명']]
                if not contrib.empty:
                    st.caption(f"  원가 기여도: {int(contrib.iloc[0]['총원가기여도']):,}원")
            st.caption(f"  💡 재료 단가 재협상 또는 레시피 최적화를 고려하세요.")
    
    if high_cost_menus.empty:
        st.success("🎉 모든 메뉴의 원가율이 35% 미만입니다!")


def _render_zone_i(menu_df: pd.DataFrame, recipe_df: pd.DataFrame, ingredient_df: pd.DataFrame):
    """ZONE I: 원가 구조 입력 현황"""
    render_section_header("원가 구조 입력 현황", "📋")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("메뉴 수", len(menu_df))
    with col2:
        st.metric("레시피 수", len(recipe_df))
    with col3:
        st.metric("재료 수", len(ingredient_df))
    
    if menu_df.empty or recipe_df.empty or ingredient_df.empty:
        st.info("원가를 계산하려면 메뉴, 레시피, 재료 데이터가 모두 필요합니다.")
        if st.button("메뉴 등록으로 이동", key="go_menu"):
            st.session_state["current_page"] = "메뉴 등록"
            st.rerun()


def render_cost_overview():
    """원가 파악 페이지 렌더링 (고도화 ZONE A~I)"""
    render_page_header("원가 분석", "💰")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'], store_id=store_id)
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'], store_id=store_id)
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'], store_id=store_id)
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'], store_id=store_id)
    
    # 원가 계산
    cost_df = pd.DataFrame()
    cost_contribution_df = pd.DataFrame()
    if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        if not daily_sales_df.empty:
            cost_contribution_df = _calculate_cost_contribution(cost_df, daily_sales_df, 30)
    
    # ZONE 렌더링
    _render_zone_a(cost_df, cost_contribution_df)
    render_section_divider()
    _render_zone_b(cost_df, recipe_df, ingredient_df)
    render_section_divider()
    _render_zone_c(cost_df, daily_sales_df)
    render_section_divider()
    _render_zone_d(cost_df, daily_sales_df)
    render_section_divider()
    _render_zone_e(cost_df, recipe_df, ingredient_df)
    render_section_divider()
    _render_zone_f(cost_df, ingredient_df)
    render_section_divider()
    _render_zone_g(cost_df)
    render_section_divider()
    _render_zone_h(cost_df, cost_contribution_df)
    render_section_divider()
    _render_zone_i(menu_df, recipe_df, ingredient_df)
