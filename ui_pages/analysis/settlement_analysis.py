"""
실제정산 분석 페이지
실제정산 입력 데이터 기반 성과 분석 (목표 vs 실제, 월간 성적표, 트렌드 등)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header, render_section_header, render_section_divider, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import (
    load_actual_settlement_items,
    load_monthly_sales_total,
    get_fixed_costs,
    get_variable_cost_ratio,
    load_csv,
    load_expense_structure,
)
from src.auth import get_current_store_id

bootstrap(page_title="실제정산 분석")


def _total_actual_costs_from_items(items):
    """actual_settlement_items 기반 총 비용 (amount 합계)"""
    total = 0.0
    for it in items or []:
        a = it.get("amount")
        if a is not None:
            total += float(a)
    return total


def render_settlement_analysis():
    """실제정산 분석 페이지 렌더링"""
    render_page_header("실제정산 분석", "🧾")

    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    year = current_year_kst()
    month = current_month_kst()

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input("연도", min_value=2020, max_value=2100, value=year, key="settlement_analysis_year")
    with col2:
        selected_month = st.number_input("월", min_value=1, max_value=12, value=month, key="settlement_analysis_month")

    render_section_divider()

    # 데이터 로드
    items = load_actual_settlement_items(store_id, selected_year, selected_month)
    actual_sales = 0.0
    try:
        actual_sales = load_monthly_sales_total(store_id, selected_year, selected_month) or 0.0
    except Exception:
        pass
    actual_costs = _total_actual_costs_from_items(items)

    targets_df = load_csv(
        "targets.csv",
        default_columns=["연도", "월", "목표매출", "목표원가율", "목표인건비율", "목표임대료율", "목표기타비용율", "목표순이익률"],
        store_id=store_id,
    )
    target_sales = 0.0
    if not targets_df.empty:
        tr = targets_df[(targets_df["연도"] == selected_year) & (targets_df["월"] == selected_month)]
        target_sales = float(safe_get_value(tr, "목표매출", 0) or 0)

    # 목표 비용: 고정비+변동비 근사 (실제정산 없으면 expense_structure 기반)
    fixed = get_fixed_costs(store_id, selected_year, selected_month) or 0.0
    var_ratio = get_variable_cost_ratio(store_id, selected_year, selected_month) or 0.0
    target_costs_approx = fixed + (actual_sales * (var_ratio / 100)) if actual_sales and var_ratio else fixed
    if items:
        target_costs_approx = None  # 실제정산 입력이 있으면 "목표 비용"은 별도 정의 필요

    # ZONE A: 목표 vs 실제 요약
    render_section_header("목표 vs 실제", "📊")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("목표 매출", f"{int(target_sales):,}원" if target_sales else "—")
    with c2:
        st.metric("실제 매출", f"{int(actual_sales):,}원" if actual_sales else "—")
    with c3:
        st.metric("실제 비용", f"{int(actual_costs):,}원" if actual_costs else "—")
    with c4:
        profit = actual_sales - actual_costs if (actual_sales or actual_costs) else None
        st.metric("순이익", f"{int(profit):,}원" if profit is not None else "—")

    if target_sales and target_sales > 0 and actual_sales:
        ratio = (actual_sales / target_sales) * 100
        st.caption(f"📈 목표 대비 매출 달성률: **{ratio:.1f}%**")

    render_section_divider()

    # ZONE B: 월간 성적표 상세
    render_section_header("월간 성적표 상세", "📋")
    if not items:
        st.info("이번 달 실제정산이 아직 입력되지 않았습니다. **실제정산** 페이지에서 비용을 입력한 뒤 분석 결과가 채워집니다.")
        if st.button("🧾 실제정산 입력으로 이동", key="settlement_analysis_go_input"):
            st.session_state["current_page"] = "실제정산"
            st.rerun()
    else:
        st.caption(f"입력된 비용 항목 **{len(items)}**개 기준으로 집계되었습니다.")
        
        # 카테고리별 비용 분석
        expense_df = load_expense_structure(selected_year, selected_month, store_id)
        if not expense_df.empty and "category" in expense_df.columns and "amount" in expense_df.columns:
            st.markdown("**카테고리별 비용**")
            cat_totals = {}
            for cat in ["임차료", "인건비", "재료비", "공과금", "부가세&카드수수료"]:
                sub = expense_df[expense_df["category"] == cat]
                cat_totals[cat] = float(sub["amount"].sum()) if not sub.empty else 0.0
            
            cat_df = pd.DataFrame({
                "카테고리": list(cat_totals.keys()),
                "금액": list(cat_totals.values())
            })
            cat_df = cat_df[cat_df["금액"] > 0]
            if not cat_df.empty:
                st.bar_chart(cat_df.set_index("카테고리")["금액"], height=250)
                st.dataframe(cat_df, use_container_width=True, hide_index=True)
        
        # 수익성 분석
        if actual_sales > 0:
            cost_rate = (actual_costs / actual_sales * 100) if actual_sales > 0 else 0
            profit_rate = (profit / actual_sales * 100) if profit is not None and actual_sales > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("비용률", f"{cost_rate:.1f}%")
            with col2:
                st.metric("이익률", f"{profit_rate:.1f}%")
            with col3:
                st.metric("매출 대비 비용", f"{int(actual_costs):,}원" if actual_costs else "—")

    render_section_divider()
    
    # ZONE C: 월별 트렌드 (최근 3개월)
    render_section_header("월별 트렌드 (최근 3개월)", "📈")
    try:
        months_data = []
        for i in range(3):
            check_year = selected_year
            check_month = selected_month - i
            if check_month <= 0:
                check_month += 12
                check_year -= 1
            
            m_sales = 0.0
            try:
                m_sales = load_monthly_sales_total(store_id, check_year, check_month) or 0.0
            except Exception:
                pass
            
            m_items = load_actual_settlement_items(store_id, check_year, check_month) or []
            m_costs = sum(float(it.get("amount") or 0) for it in m_items)
            m_profit = m_sales - m_costs
            
            months_data.append({
                "월": f"{check_year}-{check_month:02d}",
                "매출": m_sales,
                "비용": m_costs,
                "순이익": m_profit
            })
        
        trend_df = pd.DataFrame(months_data)
        if not trend_df.empty:
            st.line_chart(trend_df.set_index("월")[["매출", "비용", "순이익"]], height=300)
    except Exception:
        st.caption("트렌드 데이터를 불러올 수 없습니다.")

    st.markdown("---")
    st.caption("💡 비용 입력·수정은 **실제정산** 페이지에서 하세요. PDF 성적표는 실제정산 페이지에서 다운로드할 수 있습니다.")
