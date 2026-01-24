"""
비용 분석 페이지
목표 비용구조 입력 데이터 기반 비용 분석 (손익분기점, 고정비/변동비, 월간 집계 등)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header, render_section_header, render_section_divider, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import (
    load_expense_structure,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_monthly_sales_total,
    load_csv,
)
from src.auth import get_current_store_id

bootstrap(page_title="비용 분석")


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

    # ZONE A: 핵심 지표 카드
    render_section_header("핵심 지표", "📊")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("고정비", f"{int(fixed):,}원" if fixed else "—", help="임차료·인건비·공과금 등")
    with c2:
        st.metric("변동비율", f"{variable_ratio:.1f}%" if variable_ratio else "—", help="매출 대비 변동비")
    with c3:
        st.metric("손익분기 매출", f"{int(breakeven):,}원" if breakeven else "—", help="고정비/(1-변동비율)")
    with c4:
        ratio = (monthly_sales / breakeven * 100) if breakeven and breakeven > 0 else None
        delta = f"{ratio:.0f}% 대비" if ratio is not None else "—"
        st.metric("이번 달 매출", f"{int(monthly_sales):,}원" if monthly_sales else "—", delta=delta)

    render_section_divider()

    # ZONE B: 목표매출 달성 시 비용구조
    render_section_header("목표매출 달성 시 비용구조", "🎯")
    if target_sales and target_sales > 0 and (fixed or variable_ratio):
        var_amount = target_sales * (variable_ratio / 100) if variable_ratio else 0
        total_cost = fixed + var_amount
        profit = target_sales - total_cost
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
        st.markdown("**비용 구조**")
        st.markdown(f"""
        | 항목 | 금액 | 비고 |
        |------|------|------|
        | 고정비 | {int(fixed):,}원 | 임차료·인건비·공과금 |
        | 변동비 ({(variable_ratio or 0):.1f}%) | {int(var_amount):,}원 | 재료비·부가세&카드수수료 |
        | **총 비용** | **{int(total_cost):,}원** | |
        """)
        
        # 비용 구조 파이 차트 (간단 버전)
        if total_cost > 0:
            fixed_pct = (fixed / total_cost * 100) if total_cost > 0 else 0
            var_pct = (var_amount / total_cost * 100) if total_cost > 0 else 0
            chart_data = pd.DataFrame({
                "구분": ["고정비", "변동비"],
                "비율": [fixed_pct, var_pct]
            })
            st.bar_chart(chart_data.set_index("구분")["비율"], height=200)
    else:
        st.info("목표 매출을 설정하고, 고정비·변동비를 입력하면 시뮬레이션 결과가 표시됩니다. → 목표 비용 구조 입력")
        if st.button("🧾 목표 비용 구조 입력으로 이동", key="cost_analysis_go_target_btn"):
            st.session_state["current_page"] = "목표 비용구조"
            st.rerun()

    render_section_divider()

    # ZONE C: 비용 구조 입력 현황 (5개 카테고리)
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
            for cat in ["임차료", "인건비", "재료비", "공과금", "부가세&카드수수료"]:
                sub = expense_df[expense_df["category"] == cat]
                total = float(sub["amount"].sum()) if not sub.empty else 0.0
                st.caption(f"**{cat}**: {int(total):,}원")
        elif has_amt:
            total = float(expense_df["amount"].sum())
            st.caption(f"**비용 합계**: {int(total):,}원")

    render_section_divider()
    
    # ZONE D: 매출 수준별 시뮬레이션
    render_section_header("매출 수준별 비용·영업이익 시뮬레이션", "📈")
    if fixed or variable_ratio:
        sim_sales = st.number_input(
            "시뮬레이션 매출 (원)",
            min_value=0,
            value=int(target_sales) if target_sales > 0 else int(breakeven) if breakeven > 0 else 10000000,
            step=1000000,
            key="cost_analysis_sim_sales",
            help="다양한 매출 수준에서 비용과 이익을 확인하세요"
        )
        if sim_sales > 0:
            sim_var = sim_sales * (variable_ratio / 100) if variable_ratio else 0
            sim_total = fixed + sim_var
            sim_profit = sim_sales - sim_total
            sim_rate = (sim_profit / sim_sales * 100) if sim_sales > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 비용", f"{int(sim_total):,}원")
            with col2:
                st.metric("영업이익", f"{int(sim_profit):,}원", delta=f"{sim_rate:.1f}%")
            with col3:
                st.metric("손익분기 대비", f"{((sim_sales / breakeven) * 100):.0f}%" if breakeven and breakeven > 0 else "—")
    else:
        st.caption("고정비·변동비를 입력하면 시뮬레이션이 가능합니다.")
    
    st.markdown("---")
    st.caption("💡 상세 비용 입력·수정은 **목표 비용 구조 입력** 페이지에서 하세요.")
