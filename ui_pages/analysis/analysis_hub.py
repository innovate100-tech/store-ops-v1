"""
분석 허브 페이지
핵심 자료(매출·비용·실제정산·원가·재고·재료사용) 요약 노출 + 세부분석 링크
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import (
    load_monthly_sales_total,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_actual_settlement_items,
    load_csv,
)
from src.analytics import calculate_menu_cost, calculate_ingredient_usage
from src.auth import get_current_store_id

bootstrap(page_title="분석 허브")


def _safe_monthly_sales(store_id, year, month):
    try:
        return load_monthly_sales_total(store_id, year, month) or 0.0
    except Exception:
        return 0.0


def _safe_target_sales(store_id, year, month):
    try:
        df = load_csv(
            "targets.csv",
            default_columns=["연도", "월", "목표매출"],
            store_id=store_id,
        )
        if df.empty:
            return 0.0
        r = df[(df["연도"] == year) & (df["월"] == month)]
        if r.empty:
            return 0.0
        return float(r.iloc[0].get("목표매출", 0) or 0)
    except Exception:
        return 0.0


def _safe_actual_costs(store_id, year, month):
    try:
        items = load_actual_settlement_items(store_id, year, month) or []
        return sum(float(it.get("amount") or 0) for it in items)
    except Exception:
        return 0.0


def _hub_card(title: str, value: str, sub: str, page_key: str, help_text: str = "", icon: str = "📊"):
    """분석 허브 카드 렌더링 (시각적으로 보기 좋게)"""
    sub_html = f'<div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.8rem;">{sub}</div>' if sub else ''
    help_html = f'<div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">{help_text}</div>' if help_text else ''
    st.markdown(f"""
    <div style="padding: 1.2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                border-radius: 12px; border: 1px solid rgba(148,163,184,0.3); 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <h3 style="margin: 0; font-size: 1rem; font-weight: 600; color: #e5e7eb;">{title}</h3>
        </div>
        <div style="font-size: 1.3rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem;">
            {value if value else "—"}
        </div>
        {sub_html}
        {help_html}
    </div>
    """, unsafe_allow_html=True)
    if st.button("자세히 보기", key=f"hub_go_{page_key}", use_container_width=True, type="primary"):
        st.session_state["current_page"] = page_key
        st.rerun()


def render_analysis_hub():
    """분석 허브 페이지 렌더링"""
    render_page_header("📊 분석 허브", "📊")

    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    st.markdown("""
    <div style="padding: 1rem; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 8px; margin-bottom: 1.5rem;">
        <p style="margin: 0; font-size: 1rem; line-height: 1.6;">
            <strong>분석은 가게 숫자를 해석하는 일입니다.</strong><br>
            핵심만 먼저 보세요. 세부는 아래 '세부분석선택'에서 골라 들어가면 됩니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    year = current_year_kst()
    month = current_month_kst()

    # 데이터 로드 (경량)
    monthly_sales = _safe_monthly_sales(store_id, year, month)
    target_sales = _safe_target_sales(store_id, year, month)
    actual_costs = _safe_actual_costs(store_id, year, month)
    fixed = get_fixed_costs(store_id, year, month) or 0.0
    var_ratio = get_variable_cost_ratio(store_id, year, month) or 0.0
    breakeven = calculate_break_even_sales(store_id, year, month) or 0.0

    menu_df = load_csv("menu_master.csv", default_columns=["메뉴명", "판매가"], store_id=store_id)
    recipe_df = load_csv("recipes.csv", default_columns=["메뉴명", "재료명", "사용량"], store_id=store_id)
    ing_df = load_csv("ingredient_master.csv", default_columns=["재료명", "단위", "단가"], store_id=store_id)
    inv_df = load_csv("inventory.csv", default_columns=["재료명", "현재고", "안전재고"], store_id=store_id)
    sales_df = load_csv("daily_sales_items.csv", default_columns=["날짜", "메뉴명", "판매수량"], store_id=store_id)

    cost_df = pd.DataFrame()
    if not menu_df.empty and not recipe_df.empty and not ing_df.empty:
        try:
            cost_df = calculate_menu_cost(menu_df, recipe_df, ing_df)
        except Exception:
            pass

    usage_df = pd.DataFrame()
    if not sales_df.empty and not recipe_df.empty:
        try:
            usage_df = calculate_ingredient_usage(sales_df, recipe_df)
        except Exception:
            pass

    # 품절 위험 개수 (현재고 < 안전재고)
    danger_count = 0
    if not inv_df.empty and "현재고" in inv_df.columns and "안전재고" in inv_df.columns:
        for _, row in inv_df.iterrows():
            cur = row.get("현재고")
            safe = row.get("안전재고")
            if safe and (cur is None or (float(cur) < float(safe))):
                danger_count += 1

    # ---------- ZONE A: 핵심 자료 6카드 ----------
    st.markdown("### 한눈에 보는 핵심 지표")
    st.caption("이번 달 기준 요약입니다. 자세한 내용은 각 '자세히 보기'에서 확인하세요.")

    c1, c2, c3 = st.columns(3)
    with c1:
        sales_val = f"{int(monthly_sales):,}원" if monthly_sales else "—"
        ratio = f"목표 {((monthly_sales / target_sales) * 100):.0f}%" if target_sales and target_sales > 0 else ""
        _hub_card("매출", sales_val, ratio, "매출 관리", "이번 달 누적 매출", "💰")
    with c2:
        be_val = f"{int(breakeven):,}원" if breakeven else "—"
        sub = f"매출 {((monthly_sales / breakeven) * 100):.0f}%" if breakeven and breakeven > 0 and monthly_sales else ""
        _hub_card("비용·손익", be_val, sub, "비용 분석", "손익분기 매출", "💳")
    with c3:
        profit = monthly_sales - actual_costs if (monthly_sales or actual_costs) else None
        pv = f"{int(profit):,}원" if profit is not None else "—"
        _hub_card("실제정산", pv, "", "실제정산 분석", "순이익(실제 매출−비용)", "🧾")

    d1, d2, d3 = st.columns(3)
    with d1:
        if not cost_df.empty and "원가율" in cost_df.columns:
            high = len(cost_df[cost_df["원가율"] >= 35])
            avg = cost_df["원가율"].mean()
            val = f"고원가 {high}개<br>평균 {avg:.1f}%"
        else:
            val = "—"
        _hub_card("원가", val, "", "원가 파악", "고원가율 메뉴·평균 원가율", "💵")
    with d2:
        val = f"품절 위험<br>{danger_count}개" if inv_df is not None and not inv_df.empty and danger_count > 0 else ("재고 안정" if inv_df is not None and not inv_df.empty else "—")
        _hub_card("재고", val, "", "재고 분석", "안전재고 대비 부족", "📦")
    with d3:
        if not usage_df.empty and "재료명" in usage_df.columns and "총사용량" in usage_df.columns:
            agg = usage_df.groupby("재료명")["총사용량"].sum().nlargest(5)
            top = agg.index.tolist()
            val = "<br>".join([f"• {t}" for t in top[:3]]) if top else "—"
        else:
            val = "—"
        _hub_card("재료 사용", val or "—", "", "재료 사용량 집계", "TOP 사용 재료", "🧺")

    st.markdown("---")

    # ---------- ZONE B: 세부분석선택 (expander) ----------
    sub_items = [
        ("매출 분석", "매출 관리"),
        ("비용 분석", "비용 분석"),
        ("실제정산 분석", "실제정산 분석"),
        ("원가 분석", "원가 파악"),
        ("재고 분석", "재고 분석"),
        ("재료 사용량", "재료 사용량 집계"),
        ("판매·메뉴 분석", "판매 관리"),
        ("매출 하락 원인 찾기", "매출 하락 원인 찾기"),
        ("검진 결과 요약", "검진 결과 요약"),
        ("검진 히스토리", "검진 히스토리"),
    ]
    with st.expander("세부분석선택", expanded=False):
        st.caption("상세 분석이 필요할 때 페이지를 골라 들어가세요.")
        for label, key in sub_items:
            if st.button(label, key=f"analysis_hub_sub_{key}", use_container_width=True, type="secondary"):
                st.session_state["current_page"] = key
                st.rerun()
