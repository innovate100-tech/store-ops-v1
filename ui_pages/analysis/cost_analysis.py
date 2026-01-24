"""
비용 분석 페이지 (고도화)
목표 비용구조의 5대 핵심 비용 심층 분석 및 다른 데이터와의 통합 분석
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from calendar import monthrange
from datetime import timedelta
from src.ui_helpers import render_page_header, render_section_header, render_section_divider, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst, today_kst
from src.storage_supabase import (
    load_expense_structure,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_monthly_sales_total,
    load_csv,
    load_cost_item_templates,
    load_actual_settlement_items,
)
from src.analytics import calculate_ingredient_usage
from src.auth import get_current_store_id

bootstrap(page_title="비용 분석")

# 5대 핵심 비용 카테고리
_FIVE_CORE_CATEGORIES = ['임차료', '인건비', '공과금', '재료비', '부가세&카드수수료']
_FIXED_CATEGORIES = ['임차료', '인건비', '공과금']
_VARIABLE_CATEGORIES = ['재료비', '부가세&카드수수료']


def _load_five_core_costs(store_id: str, year: int, month: int, monthly_sales: float = None) -> dict:
    """
    5대 핵심 비용 로드 및 정규화
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        monthly_sales: 월간 매출 (None이면 자동 로드)
    
    Returns:
        dict: {
            '임차료': {'amount': float, 'rate': float, 'items': list},
            '인건비': {'amount': float, 'rate': float, 'items': list},
            '공과금': {'amount': float, 'rate': float, 'items': list},
            '재료비': {'amount': float, 'rate': float, 'items': list},
            '부가세&카드수수료': {'amount': float, 'rate': float, 'items': list},
        }
    """
    expense_df = load_expense_structure(year, month, store_id)
    if monthly_sales is None:
        monthly_sales = load_monthly_sales_total(store_id, year, month) or 0.0
    
    result = {}
    for cat in _FIVE_CORE_CATEGORIES:
        cat_df = expense_df[expense_df['category'] == cat] if not expense_df.empty and 'category' in expense_df.columns else pd.DataFrame()
        
        if cat in _FIXED_CATEGORIES:
            # 고정비: amount는 금액, rate는 매출 대비 비율
            amount = float(cat_df['amount'].sum()) if not cat_df.empty and 'amount' in cat_df.columns else 0.0
            rate = (amount / monthly_sales * 100) if monthly_sales > 0 else 0.0
        else:
            # 변동비: amount는 비율(%), rate도 동일, 실제 금액은 매출 × rate
            rate = float(cat_df['amount'].sum()) if not cat_df.empty and 'amount' in cat_df.columns else 0.0  # % 단위
            amount = (monthly_sales * rate / 100) if monthly_sales > 0 else 0.0
        
        items = cat_df.to_dict('records') if not cat_df.empty else []
        
        result[cat] = {
            'amount': amount,
            'rate': rate,
            'items': items
        }
    
    return result


def _calculate_costs_by_sales_level(sales_level: float, five_core_costs: dict, expense_df: pd.DataFrame = None) -> dict:
    """
    매출 수준별 5대 비용 계산
    
    Args:
        sales_level: 시뮬레이션 매출 (원)
        five_core_costs: _load_five_core_costs() 결과
        expense_df: expense_structure DataFrame (고정비 원본 금액 추출용, 선택)
    
    Returns:
        dict: {
            '임차료': float,
            '인건비': float,
            '공과금': float,
            '재료비': float,
            '부가세&카드수수료': float,
            '총비용': float,
            '영업이익': float
        }
    """
    # 고정비: expense_structure의 원본 금액 사용 (매출과 무관)
    if expense_df is not None and not expense_df.empty and 'category' in expense_df.columns and 'amount' in expense_df.columns:
        rent_df = expense_df[expense_df['category'] == '임차료']
        labor_df = expense_df[expense_df['category'] == '인건비']
        utility_df = expense_df[expense_df['category'] == '공과금']
        rent = float(rent_df['amount'].sum()) if not rent_df.empty else 0.0
        labor = float(labor_df['amount'].sum()) if not labor_df.empty else 0.0
        utility = float(utility_df['amount'].sum()) if not utility_df.empty else 0.0
    else:
        # fallback: five_core_costs의 amount 사용 (이미 expense_structure 원본 금액)
        rent = five_core_costs.get('임차료', {}).get('amount', 0.0)
        labor = five_core_costs.get('인건비', {}).get('amount', 0.0)
        utility = five_core_costs.get('공과금', {}).get('amount', 0.0)
    
    # 변동비: 매출 × 비율(%)
    material_rate = five_core_costs.get('재료비', {}).get('rate', 0.0)  # % 단위
    fee_rate = five_core_costs.get('부가세&카드수수료', {}).get('rate', 0.0)  # % 단위
    
    material = sales_level * (material_rate / 100) if material_rate else 0.0
    fee = sales_level * (fee_rate / 100) if fee_rate else 0.0
    
    total_cost = rent + labor + utility + material + fee
    profit = sales_level - total_cost
    
    return {
        '임차료': rent,
        '인건비': labor,
        '공과금': utility,
        '재료비': material,
        '부가세&카드수수료': fee,
        '총비용': total_cost,
        '영업이익': profit
    }


def _compare_target_vs_actual(store_id: str, year: int, month: int, target_costs: dict, monthly_sales: float) -> dict:
    """
    목표 비용구조 vs 실제정산 비교
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        target_costs: _load_five_core_costs() 결과 (목표)
        monthly_sales: 실제 매출
    
    Returns:
        dict: {
            '임차료': {'target_amount': float, 'actual_amount': float, 'diff_amount': float, ...},
            ...
        }
    """
    try:
        actual_items = load_actual_settlement_items(store_id, year, month)
        templates = load_cost_item_templates(store_id)
    except Exception:
        return {}
    
    actual_costs = {}
    for cat in _FIVE_CORE_CATEGORIES:
        cat_templates = [t for t in templates if t.get('category') == cat and t.get('is_active', True)]
        cat_amount = 0.0
        cat_rate = 0.0
        
        for template in cat_templates:
            template_id = template.get('id')
            actual_item = next((a for a in actual_items if str(a.get('template_id')) == str(template_id)), None)
            
            if actual_item:
                if actual_item.get('amount'):
                    cat_amount += float(actual_item['amount'] or 0)
                elif actual_item.get('percent'):
                    cat_rate += float(actual_item['percent'] or 0)
        
        if cat in _FIXED_CATEGORIES:
            # 고정비: amount 사용
            actual_amount = cat_amount
            actual_rate = (actual_amount / monthly_sales * 100) if monthly_sales > 0 else 0.0
        else:
            # 변동비: rate 사용, amount는 계산
            actual_rate = cat_rate
            actual_amount = (monthly_sales * actual_rate / 100) if monthly_sales > 0 else 0.0
        
        target_amount = target_costs.get(cat, {}).get('amount', 0.0)
        target_rate = target_costs.get(cat, {}).get('rate', 0.0)
        
        actual_costs[cat] = {
            'target_amount': target_amount,
            'actual_amount': actual_amount,
            'diff_amount': actual_amount - target_amount,
            'target_rate': target_rate,
            'actual_rate': actual_rate,
            'diff_rate': actual_rate - target_rate
        }
    
    return actual_costs


def render_cost_analysis():
    """비용 분석 페이지 렌더링"""
    render_page_header("비용 분석", "💰")

    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    year = current_year_kst()
    month = current_month_kst()

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input("연도", min_value=2020, max_value=2100, value=year, key="cost_analysis_year")
    with col2:
        selected_month = st.number_input("월", min_value=1, max_value=12, value=month, key="cost_analysis_month")

    render_section_divider()

    # 데이터 로드
    fixed = get_fixed_costs(store_id, selected_year, selected_month) or 0.0
    variable_ratio = get_variable_cost_ratio(store_id, selected_year, selected_month) or 0.0
    breakeven = calculate_break_even_sales(store_id, selected_year, selected_month) or 0.0
    monthly_sales = 0.0
    try:
        monthly_sales = load_monthly_sales_total(store_id, selected_year, selected_month) or 0.0
    except Exception:
        pass

    targets_df = load_csv(
        "targets.csv",
        default_columns=["연도", "월", "목표매출", "목표원가율", "목표인건비율", "목표임대료율", "목표기타비용율", "목표순이익률"],
        store_id=store_id,
    )
    target_sales = 0.0
    if not targets_df.empty:
        tr = targets_df[(targets_df["연도"] == selected_year) & (targets_df["월"] == selected_month)]
        target_sales = float(safe_get_value(tr, "목표매출", 0) or 0)

    expense_df = load_expense_structure(selected_year, selected_month, store_id)
    five_core_costs = _load_five_core_costs(store_id, selected_year, selected_month, monthly_sales)
    total_cost = sum(cat.get('amount', 0) for cat in five_core_costs.values())
    cost_rate = (total_cost / monthly_sales * 100) if monthly_sales > 0 else 0.0

    # ZONE A: 핵심 지표 (강화: 5대 비용 카드 추가)
    render_section_header("핵심 지표", "📊")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("고정비", f"{int(fixed):,}원" if fixed else "—", help="임차료·인건비·공과금 등")
    with c2:
        st.metric("변동비율", f"{variable_ratio * 100:.1f}%" if variable_ratio and variable_ratio > 0 else "—", help="매출 대비 변동비")
    with c3:
        st.metric("손익분기 매출", f"{int(breakeven):,}원" if breakeven else "—", help="고정비/(1-변동비율)")
    with c4:
        ratio = (monthly_sales / breakeven * 100) if breakeven and breakeven > 0 else None
        delta = f"{ratio:.0f}% 대비" if ratio is not None else "—"
        st.metric("이번 달 매출", f"{int(monthly_sales):,}원" if monthly_sales else "—", delta=delta)
    
    st.markdown("---")
    st.markdown("**5대 핵심 비용 요약**")
    cost_cols = st.columns(5)
    for idx, cat in enumerate(_FIVE_CORE_CATEGORIES):
        with cost_cols[idx]:
            cat_data = five_core_costs.get(cat, {})
            amount = cat_data.get('amount', 0.0)
            rate = cat_data.get('rate', 0.0)
            if cat in _FIXED_CATEGORIES:
                # 고정비: 금액 중심
                st.metric(cat, f"{int(amount):,}원", delta=f"{rate:.1f}%")
            else:
                # 변동비: 비율 중심
                st.metric(cat, f"{rate:.2f}%", delta=f"{int(amount):,}원")
    
    st.caption(f"**총 비용**: {int(total_cost):,}원 · **비용률**: {cost_rate:.1f}%")

    render_section_divider()

    # ZONE B: 5대 핵심 비용 상세 분석
    render_section_header("5대 핵심 비용 상세 분석", "📊")
    if expense_df.empty:
        st.info("💡 비용 구조가 입력되지 않았습니다. **목표 비용 구조 입력**에서 설정하세요.")
    else:
        tabs = st.tabs(_FIVE_CORE_CATEGORIES)
        for idx, cat in enumerate(_FIVE_CORE_CATEGORIES):
            with tabs[idx]:
                cat_data = five_core_costs.get(cat, {})
                amount = cat_data.get('amount', 0.0)
                rate = cat_data.get('rate', 0.0)
                items = cat_data.get('items', [])
                
                col1, col2 = st.columns(2)
                if cat in _FIXED_CATEGORIES:
                    # 고정비: 금액 중심
                    with col1:
                        st.metric("금액", f"{int(amount):,}원")
                    with col2:
                        st.metric("매출 대비 비율", f"{rate:.2f}%")
                else:
                    # 변동비: 비율 중심
                    with col1:
                        st.metric("비율", f"{rate:.2f}%")
                    with col2:
                        st.metric("금액 (현재 매출 기준)", f"{int(amount):,}원")
                
                if items:
                    st.markdown("**세부 항목**")
                    items_df = pd.DataFrame(items)
                    if 'item_name' in items_df.columns and 'amount' in items_df.columns:
                        display_df = items_df[['item_name', 'amount']].copy()
                        display_df.columns = ['항목명', '금액' if cat in _FIXED_CATEGORIES else '비율(%)']
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 전월 대비 (간단 버전)
                if selected_month == 1:
                    prev_year, prev_month = selected_year - 1, 12
                else:
                    prev_year, prev_month = selected_year, selected_month - 1
                try:
                    prev_costs = _load_five_core_costs(store_id, prev_year, prev_month)
                    if cat in _FIXED_CATEGORIES:
                        prev_amount = prev_costs.get(cat, {}).get('amount', 0.0)
                        if prev_amount > 0:
                            change = ((amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0.0
                            st.caption(f"📈 전월 대비: **{change:+.1f}%** ({int(prev_amount):,}원 → {int(amount):,}원)")
                    else:
                        prev_rate = prev_costs.get(cat, {}).get('rate', 0.0)
                        if prev_rate > 0:
                            change = rate - prev_rate
                            st.caption(f"📈 전월 대비: **{change:+.2f}%p** ({prev_rate:.2f}% → {rate:.2f}%)")
                except Exception:
                    pass

    render_section_divider()

    # ZONE C: 비용 구조 시각화
    render_section_header("비용 구조 시각화", "📈")
    if not expense_df.empty and total_cost > 0:
        # 파이 차트: 5대 비용 비중
        pie_data = pd.DataFrame({
            '카테고리': _FIVE_CORE_CATEGORIES,
            '금액': [five_core_costs[cat].get('amount', 0) for cat in _FIVE_CORE_CATEGORIES]
        })
        st.markdown("**5대 비용 비중 (금액 기준)**")
        st.bar_chart(pie_data.set_index('카테고리')['금액'], height=250)
        
        # 바 차트: 금액 + 비율
        if monthly_sales > 0:
            bar_data = pd.DataFrame({
                '카테고리': _FIVE_CORE_CATEGORIES,
                '금액(만원)': [five_core_costs[cat].get('amount', 0) / 10000 for cat in _FIVE_CORE_CATEGORIES],
                '비율(%)': [five_core_costs[cat].get('rate', 0) for cat in _FIVE_CORE_CATEGORIES]
            })
            st.markdown("**카테고리별 금액 및 비율**")
            st.bar_chart(bar_data.set_index('카테고리')[['금액(만원)', '비율(%)']], height=250)
    else:
        st.caption("비용 구조 데이터가 없으면 차트가 표시되지 않습니다.")

    render_section_divider()

    # ZONE D: 목표매출 달성 시 비용구조 (강화: 5대 비용 각각 표시)
    render_section_header("목표매출 달성 시 비용구조", "🎯")
    if target_sales and target_sales > 0 and (fixed or variable_ratio):
        target_costs = _calculate_costs_by_sales_level(target_sales, five_core_costs, expense_df)
        profit = target_costs['영업이익']
        profit_rate = (profit / target_sales * 100) if target_sales else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="padding: 1.2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                        border-radius: 12px; border: 1px solid rgba(148,163,184,0.3); color: #e5e7eb;">
                <div style="font-size: 0.9rem; margin-bottom: 0.8rem; opacity: 0.9;">목표 매출</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff;">{int(target_sales):,}원</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="padding: 1.2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                        border-radius: 12px; border: 1px solid rgba(148,163,184,0.3); color: #e5e7eb;">
                <div style="font-size: 0.9rem; margin-bottom: 0.8rem; opacity: 0.9;">예상 순이익</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {'#4ade80' if profit > 0 else '#f87171'};">{int(profit):,}원</div>
                <div style="font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.8;">{profit_rate:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**5대 비용 구조**")
        cost_table_data = []
        for cat in _FIVE_CORE_CATEGORIES:
            cost_amt = target_costs.get(cat, 0.0)
            cost_rate_val = (cost_amt / target_sales * 100) if target_sales > 0 else 0.0
            cost_table_data.append({
                '카테고리': cat,
                '금액': f"{int(cost_amt):,}원",
                '비율': f"{cost_rate_val:.2f}%"
            })
        cost_table_data.append({
            '카테고리': '**총 비용**',
            '금액': f"**{int(target_costs['총비용']):,}원**",
            '비율': f"**{(target_costs['총비용'] / target_sales * 100) if target_sales > 0 else 0:.2f}%**"
        })
        st.dataframe(pd.DataFrame(cost_table_data), use_container_width=True, hide_index=True)
        
        # 스택 바 차트: 5대 비용 구성
        stack_data = pd.DataFrame({
            '카테고리': _FIVE_CORE_CATEGORIES,
            '금액': [target_costs.get(cat, 0) for cat in _FIVE_CORE_CATEGORIES]
        })
        st.bar_chart(stack_data.set_index('카테고리')['금액'], height=200)
    else:
        st.info("목표 매출을 설정하고, 고정비·변동비를 입력하면 시뮬레이션 결과가 표시됩니다. → 목표 비용 구조 입력")
        if st.button("🧾 목표 비용 구조 입력으로 이동", key="cost_analysis_go_target_btn"):
            st.session_state["current_page"] = "목표 비용구조"
            st.rerun()

    render_section_divider()
    
    # ZONE E: 매출 수준별 5대 비용 시뮬레이션 (강화)
    render_section_header("매출 수준별 5대 비용 시뮬레이션", "📈")
    if fixed or variable_ratio:
        sim_sales = st.number_input(
            "시뮬레이션 매출 (원)",
            min_value=0,
            value=int(target_sales) if target_sales > 0 else int(breakeven) if breakeven > 0 else 10000000,
            step=1000000,
            key="cost_analysis_sim_sales",
            help="다양한 매출 수준에서 5대 비용 각각의 변화를 확인하세요"
        )
        if sim_sales > 0:
            sim_costs = _calculate_costs_by_sales_level(sim_sales, five_core_costs, expense_df)
            sim_profit = sim_costs['영업이익']
            sim_rate = (sim_profit / sim_sales * 100) if sim_sales > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 비용", f"{int(sim_costs['총비용']):,}원")
            with col2:
                st.metric("영업이익", f"{int(sim_profit):,}원", delta=f"{sim_rate:.1f}%")
            with col3:
                st.metric("손익분기 대비", f"{((sim_sales / breakeven) * 100):.0f}%" if breakeven and breakeven > 0 else "—")
            
            st.markdown("---")
            st.markdown("**5대 비용 상세**")
            sim_table_data = []
            for cat in _FIVE_CORE_CATEGORIES:
                cost_amt = sim_costs.get(cat, 0.0)
                cost_rate_val = (cost_amt / sim_sales * 100) if sim_sales > 0 else 0.0
                sim_table_data.append({
                    '카테고리': cat,
                    '금액': f"{int(cost_amt):,}원",
                    '비율': f"{cost_rate_val:.2f}%"
                })
            sim_table_data.append({
                '카테고리': '**총 비용**',
                '금액': f"**{int(sim_costs['총비용']):,}원**",
                '비율': f"**{(sim_costs['총비용'] / sim_sales * 100) if sim_sales > 0 else 0:.2f}%**"
            })
            st.dataframe(pd.DataFrame(sim_table_data), use_container_width=True, hide_index=True)
            
            # 여러 매출 수준 비교
            st.markdown("---")
            st.markdown("**여러 매출 수준 비교**")
            comparison_levels = []
            if breakeven > 0:
                comparison_levels.append(('손익분기', breakeven))
            if target_sales > 0:
                comparison_levels.append(('목표 매출', target_sales))
            if monthly_sales > 0:
                comparison_levels.append(('현재 매출', monthly_sales))
            comparison_levels.append(('시뮬레이션', sim_sales))
            
            comparison_data = []
            for label, sales_val in comparison_levels:
                comp_costs = _calculate_costs_by_sales_level(sales_val, five_core_costs, expense_df)
                comparison_data.append({
                    '매출 수준': label,
                    '매출': f"{int(sales_val):,}원",
                    '임차료': f"{int(comp_costs['임차료']):,}원",
                    '인건비': f"{int(comp_costs['인건비']):,}원",
                    '공과금': f"{int(comp_costs['공과금']):,}원",
                    '재료비': f"{int(comp_costs['재료비']):,}원",
                    '부가세&카드': f"{int(comp_costs['부가세&카드수수료']):,}원",
                    '총비용': f"{int(comp_costs['총비용']):,}원",
                    '영업이익': f"{int(comp_costs['영업이익']):,}원"
                })
            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
            
            # 스택 바 차트: 여러 매출 수준별 5대 비용 구성
            stack_comparison = pd.DataFrame({
                '매출 수준': [label for label, _ in comparison_levels],
                '임차료': [_calculate_costs_by_sales_level(sales_val, five_core_costs, expense_df)['임차료'] for _, sales_val in comparison_levels],
                '인건비': [_calculate_costs_by_sales_level(sales_val, five_core_costs, expense_df)['인건비'] for _, sales_val in comparison_levels],
                '공과금': [_calculate_costs_by_sales_level(sales_val, five_core_costs, expense_df)['공과금'] for _, sales_val in comparison_levels],
                '재료비': [_calculate_costs_by_sales_level(sales_val, five_core_costs, expense_df)['재료비'] for _, sales_val in comparison_levels],
                '부가세&카드': [_calculate_costs_by_sales_level(sales_val, five_core_costs, expense_df)['부가세&카드수수료'] for _, sales_val in comparison_levels],
            })
            st.bar_chart(stack_comparison.set_index('매출 수준'), height=300)
    else:
        st.caption("고정비·변동비를 입력하면 시뮬레이션이 가능합니다.")

    render_section_divider()

    # ZONE F: 목표 vs 실제 비교
    render_section_header("목표 vs 실제 비교", "⚖️")
    if monthly_sales > 0:
        comparison = _compare_target_vs_actual(store_id, selected_year, selected_month, five_core_costs, monthly_sales)
        if comparison:
            comp_table_data = []
            for cat in _FIVE_CORE_CATEGORIES:
                comp = comparison.get(cat, {})
                target_amt = comp.get('target_amount', 0.0)
                actual_amt = comp.get('actual_amount', 0.0)
                diff_amt = comp.get('diff_amount', 0.0)
                target_rt = comp.get('target_rate', 0.0)
                actual_rt = comp.get('actual_rate', 0.0)
                diff_rt = comp.get('diff_rate', 0.0)
                
                amt_color = "🔴" if diff_amt > 0 else "🟢" if diff_amt < 0 else "⚪"
                rt_color = "🔴" if diff_rt > 0 else "🟢" if diff_rt < 0 else "⚪"
                
                comp_table_data.append({
                    '카테고리': cat,
                    '목표 금액': f"{int(target_amt):,}원",
                    '실제 금액': f"{int(actual_amt):,}원",
                    '차이': f"{amt_color} {int(diff_amt):+,}원",
                    '목표 비율': f"{target_rt:.2f}%",
                    '실제 비율': f"{actual_rt:.2f}%",
                    '비율 차이': f"{rt_color} {diff_rt:+.2f}%p"
                })
            
            st.dataframe(pd.DataFrame(comp_table_data), use_container_width=True, hide_index=True)
            
            # 초과 비용 카테고리 식별
            over_categories = [cat for cat in _FIVE_CORE_CATEGORIES if comparison.get(cat, {}).get('diff_amount', 0) > 0]
            if over_categories:
                st.warning(f"⚠️ **초과 비용 카테고리**: {', '.join(over_categories)}")
        else:
            st.info("💡 실제정산 데이터가 없으면 비교할 수 없습니다. **실제정산** 페이지에서 데이터를 입력하세요.")
    else:
        st.caption("매출 데이터가 없으면 비교할 수 없습니다.")

    render_section_divider()

    # ZONE G: 재료 사용량 연계 분석
    render_section_header("재료 사용량 연계 분석", "🥬")
    material_rate = five_core_costs.get('재료비', {}).get('rate', 0.0)
    if material_rate > 0:
        try:
            # 재료 사용량 데이터 로드
            daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'], store_id=store_id)
            recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'], store_id=store_id)
            
            if not daily_sales_df.empty and not recipe_df.empty:
                # 이번 달 데이터 필터링
                if '날짜' in daily_sales_df.columns:
                    daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
                    month_sales = daily_sales_df[
                        (daily_sales_df['날짜'].dt.year == selected_year) & 
                        (daily_sales_df['날짜'].dt.month == selected_month)
                    ]
                else:
                    month_sales = daily_sales_df
                
                if not month_sales.empty:
                    usage_df = calculate_ingredient_usage(month_sales, recipe_df)
                    if not usage_df.empty and '재료명' in usage_df.columns:
                        if '총사용량' in usage_df.columns:
                            top_ingredients = usage_df.groupby('재료명')['총사용량'].sum().nlargest(5).reset_index()
                        else:
                            top_ingredients = usage_df.groupby('재료명').size().nlargest(5).reset_index(name='사용횟수')
                        
                        st.markdown("**TOP 5 재료 사용량**")
                        st.dataframe(top_ingredients, use_container_width=True, hide_index=True)
                        
                        st.caption(f"💡 재료비율: **{material_rate:.2f}%** · 재료비 금액: **{int(five_core_costs['재료비']['amount']):,}원**")
                    else:
                        st.caption("재료 사용량 데이터 형식이 올바르지 않습니다.")
                else:
                    st.caption("이번 달 판매 데이터가 없습니다.")
            else:
                st.caption("재료 사용량 데이터가 없습니다. **일일 마감**과 **레시피**를 입력하세요.")
        except Exception as e:
            st.caption(f"재료 사용량 분석 중 오류: {str(e)}")
    else:
        st.caption("재료비율이 설정되지 않았습니다.")

    render_section_divider()

    # ZONE H: 비용 구조 최적화 시뮬레이션
    render_section_header("비용 구조 최적화 시뮬레이션", "🔧")
    if total_cost > 0:
        st.markdown("**비용 절감 시나리오**")
        with st.expander("절감 시나리오 입력", expanded=False):
            reduction_inputs = {}
            for cat in _FIVE_CORE_CATEGORIES:
                cat_data = five_core_costs.get(cat, {})
                if cat in _FIXED_CATEGORIES:
                    reduction_inputs[cat] = st.number_input(
                        f"{cat} 절감 금액 (원)",
                        min_value=0,
                        max_value=int(cat_data.get('amount', 0)),
                        value=0,
                        step=10000,
                        key=f"reduction_{cat}"
                    )
                else:
                    reduction_inputs[cat] = st.number_input(
                        f"{cat} 절감 비율 (%p)",
                        min_value=0.0,
                        max_value=cat_data.get('rate', 0),
                        value=0.0,
                        step=0.1,
                        format="%.1f",
                        key=f"reduction_{cat}"
                    )
        
        if any(v > 0 for v in reduction_inputs.values()):
            # 절감 시나리오 계산
            new_costs = {}
            total_reduction = 0.0
            for cat in _FIVE_CORE_CATEGORIES:
                cat_data = five_core_costs.get(cat, {})
                reduction = reduction_inputs.get(cat, 0)
                if cat in _FIXED_CATEGORIES:
                    new_amount = cat_data.get('amount', 0) - reduction
                    new_costs[cat] = new_amount
                    total_reduction += reduction
                else:
                    new_rate = cat_data.get('rate', 0) - reduction
                    new_amount = (monthly_sales * new_rate / 100) if monthly_sales > 0 else 0.0
                    new_costs[cat] = new_amount
                    total_reduction += (monthly_sales * reduction / 100) if monthly_sales > 0 else 0.0
            
            new_total = sum(new_costs.values())
            new_profit = monthly_sales - new_total
            current_profit = monthly_sales - total_cost
            profit_increase = new_profit - current_profit
            
            st.success(f"✅ 절감 시 예상 영업이익 증가: **{int(profit_increase):,}원** (현재 {int(current_profit):,}원 → 절감 후 {int(new_profit):,}원)")
    else:
        st.caption("비용 구조가 없으면 최적화 시뮬레이션을 할 수 없습니다.")

    render_section_divider()

    # ZONE I: 비용 구조 입력 현황 (기존 유지)
    render_section_header("비용 구조 입력 현황", "📋")
    if expense_df.empty:
        st.caption("아직 비용 구조가 입력되지 않았습니다. 목표 비용 구조 입력에서 설정하세요.")
        if st.button("🧾 목표 비용 구조 입력으로 이동", key="cost_analysis_go_target"):
            st.session_state["current_page"] = "목표 비용구조"
            st.rerun()
    else:
        has_cat = "category" in expense_df.columns
        has_amt = "amount" in expense_df.columns
        if has_cat and has_amt:
            for cat in _FIVE_CORE_CATEGORIES:
                sub = expense_df[expense_df["category"] == cat]
                total = float(sub["amount"].sum()) if not sub.empty else 0.0
                if cat in _FIXED_CATEGORIES:
                    st.caption(f"**{cat}**: {int(total):,}원")
                else:
                    st.caption(f"**{cat}**: {total:.2f}%")
        elif has_amt:
            total = float(expense_df["amount"].sum())
            st.caption(f"**비용 합계**: {int(total):,}원")
    
    st.markdown("---")
    st.caption("💡 상세 비용 입력·수정은 **목표 비용 구조 입력** 페이지에서 하세요.")
