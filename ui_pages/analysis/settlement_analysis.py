"""
실제정산 분석 페이지 (고도화)
실제정산 입력 데이터 기반 성과 분석 (목표 vs 실제, 5대 비용, 트렌드, 인사이트)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header, render_section_header, render_section_divider, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import (
    load_actual_settlement_items,
    load_cost_item_templates,
    load_monthly_sales_total,
    load_csv,
    load_expense_structure,
)
from src.auth import get_current_store_id

bootstrap(page_title="실제정산 분석")

_FIVE = ["임차료", "인건비", "공과금", "재료비", "부가세&카드수수료"]
_FIXED = ["임차료", "인건비", "공과금"]


def _build_expense_items_from_settlement(store_id: str, year: int, month: int):
    """
    템플릿 + 실제정산 항목으로 expense_items 구조 생성 (session_state 없이).
    settlement_actual의 input_type 추론 규칙과 동일.
    """
    templates = load_cost_item_templates(store_id)
    saved = load_actual_settlement_items(store_id, year, month) or []
    saved_dict = {str(it.get("template_id")): it for it in saved if it.get("template_id") is not None}

    items_by_cat = {c: [] for c in _FIVE}
    for t in templates:
        cat = t.get("category")
        if cat not in items_by_cat:
            continue
        tid = t.get("id")
        if not tid:
            continue
        item = {
            "name": t.get("item_name", ""),
            "template_id": tid,
            "input_type": "rate" if cat in ["재료비", "부가세&카드수수료"] else "amount",
            "amount": 0,
            "rate": 0.0,
        }
        s = saved_dict.get(str(tid))
        if s:
            av = float(s.get("amount") or 0)
            pv = float(s.get("percent") or 0)
            ha = s.get("amount") is not None and av > 0
            hp = s.get("percent") is not None and pv > 0
            if ha and not hp:
                item["input_type"] = "amount"
            elif hp and not ha:
                item["input_type"] = "rate"
            elif ha and hp:
                item["input_type"] = "amount"
            if s.get("amount") is not None:
                item["amount"] = int(s.get("amount") or 0)
            if s.get("percent") is not None:
                item["rate"] = float(s.get("percent") or 0)
        items_by_cat[cat].append(item)
    return items_by_cat


def _category_total(category: str, items: list, monthly_sales: float) -> float:
    """카테고리별 총액 (amount vs rate * 매출/100)."""
    total = 0.0
    for it in items:
        if it.get("input_type") == "rate":
            r = float(it.get("rate", 0) or 0)
            total += (monthly_sales * r / 100) if monthly_sales and monthly_sales > 0 else 0.0
        else:
            total += float(it.get("amount", 0) or 0)
    return total


def _actual_costs_from_settlement(store_id: str, year: int, month: int, monthly_sales: float) -> dict:
    """
    실제정산 기반 실제 비용 계산 (SSOT).
    Returns:
        has_data: bool
        category_totals: {cat: float}
        total_cost: float
        by_category: {cat: {amount, rate}}
        expense_items: {cat: [items]}
    """
    items_by_cat = _build_expense_items_from_settlement(store_id, year, month)
    category_totals = {}
    by_category = {}
    for c in _FIVE:
        amt = _category_total(c, items_by_cat[c], monthly_sales)
        category_totals[c] = amt
        rate = (amt / monthly_sales * 100) if monthly_sales and monthly_sales > 0 else 0.0
        by_category[c] = {"amount": amt, "rate": rate}
    total_cost = sum(category_totals.values())
    has_data = any(category_totals[c] != 0 for c in _FIVE)
    return {
        "has_data": has_data,
        "category_totals": category_totals,
        "total_cost": total_cost,
        "by_category": by_category,
        "expense_items": items_by_cat,
    }


def _target_costs_from_structure(store_id: str, year: int, month: int, target_sales: float) -> dict:
    """
    목표 비용 (expense_structure + 목표 매출).
    Returns:
        has_data: bool
        by_category: {cat: {amount, rate}}
        target_total_cost: float
    """
    df = load_expense_structure(year, month, store_id=store_id)
    by_category = {c: {"amount": 0.0, "rate": 0.0} for c in _FIVE}
    if df.empty or "category" not in df.columns or "amount" not in df.columns:
        return {"has_data": False, "by_category": by_category, "target_total_cost": 0.0}

    for c in _FIVE:
        sub = df[df["category"] == c]
        if sub.empty:
            continue
        raw = float(sub["amount"].sum())
        if c in _FIXED:
            by_category[c]["amount"] = raw
            by_category[c]["rate"] = (raw / target_sales * 100) if target_sales and target_sales > 0 else 0.0
        else:
            by_category[c]["rate"] = raw
            by_category[c]["amount"] = (target_sales * raw / 100) if target_sales and target_sales > 0 else 0.0

    target_total = sum(by_category[c]["amount"] for c in _FIVE)
    has_data = target_sales and target_sales > 0 and (target_total > 0 or not df.empty)
    return {"has_data": bool(has_data), "by_category": by_category, "target_total_cost": target_total}


def _settlement_scorecard(store_id: str, year: int, month: int) -> dict:
    """
    성적표 계산 (목표 vs 실제). _compute_scorecard와 동일 규칙.
    """
    actual_sales = 0.0
    try:
        actual_sales = load_monthly_sales_total(store_id, year, month) or 0.0
    except Exception:
        pass

    targets_df = load_csv(
        "targets.csv",
        default_columns=["연도", "월", "목표매출", "목표원가율", "목표인건비율", "목표임대료율", "목표기타비용율", "목표순이익률"],
        store_id=store_id,
    )
    target_sales = 0.0
    if not targets_df.empty:
        tr = targets_df[(targets_df["연도"] == year) & (targets_df["월"] == month)]
        if not tr.empty:
            target_sales = float(safe_get_value(tr, "목표매출", 0) or 0)

    actual = _actual_costs_from_settlement(store_id, year, month, actual_sales)
    target = _target_costs_from_structure(store_id, year, month, target_sales)

    has_targets = target_sales and target_sales > 0 and target["has_data"]
    has_actual = actual["has_data"]

    comparisons = {}
    for c in _FIVE:
        a = actual["by_category"][c]
        t = target["by_category"][c]
        diff_amt = a["amount"] - t["amount"]
        diff_rate = a["rate"] - t["rate"]
        if c in _FIXED:
            if diff_amt <= 0:
                grade = "GOOD"
            elif t["amount"] and diff_amt <= t["amount"] * 0.05:
                grade = "WARN"
            else:
                grade = "BAD"
        else:
            if diff_rate <= 0:
                grade = "GOOD"
            elif diff_rate <= 5.0:
                grade = "WARN"
            else:
                grade = "BAD"
        comparisons[c] = {
            "actual_amount": a["amount"],
            "target_amount": t["amount"],
            "diff_amount": diff_amt,
            "actual_rate": a["rate"],
            "target_rate": t["rate"],
            "diff_rate": diff_rate,
            "grade": grade,
        }

    ac = actual["total_cost"]
    tc = target["target_total_cost"]
    actual_cost_rate = (ac / actual_sales * 100) if actual_sales and actual_sales > 0 else 0.0
    target_cost_rate = (tc / target_sales * 100) if target_sales and target_sales > 0 else 0.0
    actual_profit = actual_sales - ac
    target_profit = target_sales - tc if target_sales else 0.0
    actual_profit_rate = (actual_profit / actual_sales * 100) if actual_sales and actual_sales > 0 else 0.0
    target_profit_rate = (target_profit / target_sales * 100) if target_sales and target_sales > 0 else 0.0
    achievement = (actual_sales / target_sales * 100) if target_sales and target_sales > 0 else 0.0

    comments = []
    if has_targets and target_sales and actual_sales:
        if achievement < 100:
            comments.append(f"매출은 목표 대비 {100 - achievement:.1f}% 미달")
        elif achievement > 100:
            comments.append(f"매출은 목표 대비 +{achievement - 100:.1f}% 초과")
        for c, comp in comparisons.items():
            if comp["grade"] in ("WARN", "BAD"):
                if c in _FIXED:
                    comments.append(f"{c}이 +{comp['diff_amount']:,.0f}원으로 초과")
                else:
                    comments.append(f"{c}율이 +{comp['diff_rate']:.1f}%p로 초과")

    return {
        "has_actual": has_actual,
        "has_targets": has_targets,
        "actual_sales": actual_sales,
        "target_sales": target_sales,
        "achievement": achievement,
        "comparisons": comparisons,
        "total_cost": {"actual": ac, "target": tc, "actual_rate": actual_cost_rate, "target_rate": target_cost_rate},
        "profit": {
            "actual": actual_profit,
            "target": target_profit,
            "actual_rate": actual_profit_rate,
            "target_rate": target_profit_rate,
        },
        "sales": {"actual": actual_sales, "target": target_sales, "achievement": achievement},
        "comments": comments,
        "actual": actual,
        "target": target,
    }


def _trend_data(store_id: str, base_year: int, base_month: int, n_months: int) -> pd.DataFrame:
    """월별 매출·실제 비용·순이익 (실제 비용은 _actual_costs_from_settlement 적용)."""
    rows = []
    for i in range(n_months):
        m = base_month - i
        y = base_year
        while m <= 0:
            m += 12
            y -= 1
        sales = 0.0
        try:
            sales = load_monthly_sales_total(store_id, y, m) or 0.0
        except Exception:
            pass
        act = _actual_costs_from_settlement(store_id, y, m, sales)
        cost = act["total_cost"]
        profit = sales - cost
        rows.append({"월": f"{y}-{m:02d}", "매출": sales, "비용": cost, "순이익": profit})
    # 과거 → 최근 순 (차트 좌→우)
    rows.reverse()
    return pd.DataFrame(rows)


def _action_items(scorecard: dict) -> list:
    """우선순위별 액션 제안 1~3개."""
    out = []
    if not scorecard.get("has_actual") or not scorecard.get("has_targets"):
        return out
    comp = scorecard.get("comparisons", {})
    hints = {
        "재료비": "재료 사용량·원가율을 확인하고, 재료 사용량 분석에서 상세 보기.",
        "인건비": "인건비 효율(시간당 매출)을 점검하세요.",
        "임차료": "임대료 재협상 또는 공간 활용도를 검토하세요.",
        "공과금": "에너지 사용량·단가를 확인하세요.",
        "부가세&카드수수료": "카드 수수료 할인 제도를 활용하세요.",
    }
    bad = [(c, comp[c]) for c in _FIVE if comp.get(c, {}).get("grade") in ("WARN", "BAD")]
    if not bad:
        return [{"label": "목표 범위 내", "hint": "모든 비용 항목이 목표 범위 내에 있습니다."}]
    def key(x):
        cat, c = x
        return c["diff_rate"] if cat not in _FIXED else c["diff_amount"]
    bad.sort(key=key, reverse=True)
    for cat, c in bad[:3]:
        if cat in _FIXED:
            out.append({"label": f"{cat} +{c['diff_amount']:,.0f}원 초과", "hint": hints.get(cat, "")})
        else:
            out.append({"label": f"{cat} +{c['diff_rate']:.1f}%p 초과", "hint": hints.get(cat, "")})
    return out


def _render_zone_a(scorecard: dict):
    """ZONE A: 핵심 지표."""
    render_section_header("핵심 지표", "📊")
    has_actual = scorecard.get("has_actual", False)
    has_targets = scorecard.get("has_targets", False)
    sa = scorecard.get("actual_sales", 0) or 0
    ta = scorecard.get("target_sales", 0) or 0
    tc = scorecard.get("total_cost", {})
    pr = scorecard.get("profit", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("목표 매출", f"{int(ta):,}원" if ta else "—")
    with c2:
        if ta and sa:
            st.metric("실제 매출", f"{int(sa):,}원", delta=f"{sa - ta:+,.0f}원", delta_color="normal" if sa >= ta else "inverse")
        else:
            st.metric("실제 매출", f"{int(sa):,}원" if sa else "—")
    with c3:
        ac = tc.get("actual", 0) or 0
        st.metric("실제 비용", f"{int(ac):,}원" if has_actual else "—")
    with c4:
        pf = pr.get("actual", 0) if pr else None
        st.metric("순이익", f"{int(pf):,}원" if pf is not None and has_actual else "—")

    if has_targets and ta and sa:
        ach = scorecard.get("achievement", 0) or 0
        st.caption(f"📈 목표 대비 매출 달성률: **{ach:.1f}%**")
    if has_targets and has_actual:
        pt, pa = pr.get("target") if pr else None, pr.get("actual") if pr else None
        pt = pt if pt is not None else 0.0
        pa = pa if pa is not None else 0.0
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.metric("목표 비용", f"{int(tc.get('target', 0) or 0):,}원")
        with cc2:
            st.metric("비용률(실제)", f"{(tc.get('actual_rate') or 0):.1f}%", delta=f"목표 {(tc.get('target_rate') or 0):.1f}%")
        with cc3:
            st.metric("목표 순이익", f"{int(pt):,}원", delta=f"실제 대비 {pa - pt:+,.0f}원", delta_color="normal" if pa >= pt else "inverse")
    if not has_actual:
        st.info("💡 **실제정산**을 입력하면 비용·순이익이 표시됩니다. 아래 버튼으로 이동하세요.")


def _render_zone_b(store_id: str, year: int, month: int, scorecard: dict):
    """ZONE B: 목표 vs 실제 성적표."""
    render_section_header("목표 vs 실제 성적표", "📋")
    has_actual = scorecard.get("has_actual", False)
    has_targets = scorecard.get("has_targets", False)

    if not has_actual:
        st.info("이번 달 **실제정산**이 아직 입력되지 않았습니다. **실제정산** 페이지에서 비용을 입력한 뒤 성적표가 채워집니다.")
        if st.button("🧾 실제정산 입력으로 이동", key="settlement_analysis_go_input"):
            st.session_state["current_page"] = "실제정산"
            st.rerun()
        return

    if not has_targets:
        st.info("💡 이번 달 **목표**가 설정되지 않았습니다. **목표 비용구조** 및 **목표 매출구조**에서 설정하면 목표 vs 실제 비교를 볼 수 있습니다.")
        return

    sales = scorecard.get("sales", {})
    tc = scorecard.get("total_cost", {})
    pr = scorecard.get("profit", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ach = sales.get("achievement", 0) or 0
        em = "🟢" if ach >= 100 else "🟡" if ach >= 90 else "🔴"
        st.metric("매출 달성률", f"{ach:.1f}%", delta=f"{sales.get('actual', 0) - sales.get('target', 0):+,.0f}원", delta_color="normal" if ach >= 100 else "inverse")
    with col2:
        dr = (tc.get("actual_rate") or 0) - (tc.get("target_rate") or 0)
        st.metric("총비용률", f"{(tc.get('actual_rate') or 0):.1f}%", delta=f"{dr:+.1f}%p", delta_color="normal" if dr <= 0 else "inverse")
    with col3:
        pa, pt = pr.get("actual", 0) or 0, pr.get("target", 0) or 0
        st.metric("순이익", f"{pa:,.0f}원", delta=f"{pa - pt:+,.0f}원", delta_color="normal" if pa >= pt else "inverse")
    with col4:
        rcmp = (pr.get("actual_rate") or 0) - (pr.get("target_rate") or 0)
        st.metric("이익률", f"{(pr.get('actual_rate') or 0):.1f}%", delta=f"{rcmp:+.1f}%p", delta_color="normal" if rcmp >= 0 else "inverse")

    if scorecard.get("comments"):
        st.info("💬 " + ", ".join(scorecard["comments"]) + "했습니다.")

    st.markdown("**5대 비용 목표 vs 실제**")
    comp = scorecard.get("comparisons", {})
    table_data = []
    for c in _FIVE:
        x = comp.get(c, {})
        ge = {"GOOD": "🟢", "WARN": "🟡", "BAD": "🔴"}.get(x.get("grade", ""), "")
        table_data.append({
            "카테고리": c,
            "목표(원)": f"{int(x.get('target_amount', 0)):,}",
            "실제(원)": f"{int(x.get('actual_amount', 0)):,}",
            "차이(원)": f"{x.get('diff_amount', 0):+,.0f}",
            "목표(%)": f"{x.get('target_rate', 0):.2f}",
            "실제(%)": f"{x.get('actual_rate', 0):.2f}",
            "차이(%p)": f"{x.get('diff_rate', 0):+.2f}",
            "등급": ge,
        })
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_zone_c(scorecard: dict, monthly_sales: float):
    """ZONE C: 5대 비용 실제 구성 (실제정산 단독)."""
    render_section_header("5대 비용 실제 구성", "📋")
    has_actual = scorecard.get("has_actual", False)
    actual = scorecard.get("actual", {})

    if not has_actual or not actual:
        st.info("**실제정산** 입력 후 5대 비용 실제 구성을 볼 수 있습니다.")
        return

    by_cat = actual.get("by_category", {})
    cat_totals = actual.get("category_totals", {})
    total = actual.get("total_cost", 0) or 0

    chart_df = pd.DataFrame({"카테고리": _FIVE, "금액": [cat_totals.get(c, 0) for c in _FIVE]})
    chart_df = chart_df[chart_df["금액"] > 0]
    if not chart_df.empty:
        st.bar_chart(chart_df.set_index("카테고리")["금액"], height=250)

    detail = []
    for c in _FIVE:
        amt = by_cat.get(c, {}).get("amount", 0) or 0
        rate = by_cat.get(c, {}).get("rate", 0) or 0
        detail.append({"카테고리": c, "금액": amt, "매출대비(%)": round(rate, 2)})
    st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True)

    with st.expander("세부 항목 (템플릿별)"):
        items = actual.get("expense_items", {})
        for c in _FIVE:
            lst = items.get(c, [])
            if not lst:
                continue
            st.markdown(f"**{c}**")
            rows = []
            for it in lst:
                name = it.get("name", "")
                if it.get("input_type") == "rate":
                    rows.append({"항목": name, "비율(%)": it.get("rate", 0), "금액(원)": ""})
                else:
                    rows.append({"항목": name, "비율(%)": "", "금액(원)": f"{int(it.get('amount', 0) or 0):,}"})
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown("")


def _render_zone_d(store_id: str, year: int, month: int):
    """ZONE D: 월별 트렌드 (3/6/12개월)."""
    render_section_header("월별 트렌드", "📈")
    sel = st.radio("기간", [3, 6, 12], format_func=lambda x: f"최근 {x}개월", horizontal=True, key="settlement_trend_months")
    n = int(sel)
    df = _trend_data(store_id, year, month, n)
    if df.empty:
        st.caption("트렌드 데이터를 불러올 수 없습니다.")
        return
    st.line_chart(df.set_index("월")[["매출", "비용", "순이익"]], height=300)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_zone_e(scorecard: dict):
    """ZONE E: 인사이트·액션 + 연계 링크."""
    render_section_header("인사이트 및 액션", "💡")
    actions = _action_items(scorecard)
    for a in actions:
        with st.container():
            st.markdown(f"**{a.get('label', '')}**")
            if a.get("hint"):
                st.caption(a["hint"])

    st.markdown("**다른 분석 보기**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 매출 분석에서 보기", key="settlement_link_sales"):
            st.session_state["current_page"] = "매출 관리"
            st.rerun()
    with c2:
        if st.button("💰 비용 분석에서 보기", key="settlement_link_cost"):
            st.session_state["current_page"] = "비용 분석"
            st.rerun()

    st.markdown("---")
    st.caption("💡 비용 입력·수정은 **실제정산** 페이지에서 하세요. PDF 성적표는 실제정산 페이지에서 다운로드할 수 있습니다.")


def render_settlement_analysis():
    """실제정산 분석 페이지 렌더링 (고도화 ZONE A–E)."""
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

    scorecard = _settlement_scorecard(store_id, selected_year, selected_month)
    actual_sales = scorecard.get("actual_sales", 0) or 0

    _render_zone_a(scorecard)
    render_section_divider()
    _render_zone_b(store_id, selected_year, selected_month, scorecard)
    render_section_divider()
    _render_zone_c(scorecard, actual_sales)
    render_section_divider()
    _render_zone_d(store_id, selected_year, selected_month)
    render_section_divider()
    _render_zone_e(scorecard)
