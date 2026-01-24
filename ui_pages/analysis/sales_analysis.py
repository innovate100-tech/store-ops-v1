"""
매출 분석 페이지 (고도화)
ZONE A~I: 핵심 지표, 목표 vs 실제, 일자별 손익표, 요일별 패턴, 트렌드, 시뮬레이션, 민감도, 자동 진단, 상세 분석
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from datetime import timedelta
from calendar import monthrange

from src.ui_helpers import render_page_header, render_section_header, render_section_divider, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst, today_kst
from src.storage_supabase import (
    load_csv,
    load_monthly_sales_total,
    load_best_available_daily_sales,
    count_unofficial_days_in_month,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
)
from src.analytics import merge_sales_visitors, calculate_correlation
from src.auth import get_current_store_id

bootstrap(page_title="매출 분석")

# 요일 한글 매핑
_WEEKDAY_KR = {
    "Monday": "월요일",
    "Tuesday": "화요일",
    "Wednesday": "수요일",
    "Thursday": "목요일",
    "Friday": "금요일",
    "Saturday": "토요일",
    "Sunday": "일요일",
}
_WEEKDAY_ORDER = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def _build_sales_and_merged(store_id):
    """best_available 일별 매출 + 방문자 병합 DataFrame 생성"""
    best = load_best_available_daily_sales(store_id=store_id)
    if best.empty:
        sales_df = pd.DataFrame(columns=["날짜", "총매출", "카드매출", "현금매출", "is_official", "source"])
    else:
        sales_df = best.copy()
        sales_df["날짜"] = pd.to_datetime(sales_df["date"])
        sales_df["총매출"] = sales_df["total_sales"]
        sales_df["카드매출"] = sales_df.get("card_sales", 0)
        sales_df["현금매출"] = sales_df.get("cash_sales", 0)
        sales_df["is_official"] = sales_df.get("is_official", True)
        sales_df["source"] = sales_df.get("source", "daily_close")

    visitors_df = load_csv("naver_visitors.csv", default_columns=["날짜", "방문자수"], store_id=store_id)
    if not visitors_df.empty and "날짜" in visitors_df.columns:
        visitors_df["날짜"] = pd.to_datetime(visitors_df["날짜"])

    try:
        merged = merge_sales_visitors(sales_df, visitors_df)
    except Exception:
        merged = pd.DataFrame()

    if not merged.empty and "날짜" in merged.columns:
        merged["날짜"] = pd.to_datetime(merged["날짜"])

    return sales_df, merged


def _month_data(merged_df, year, month):
    """선택 연·월 해당 일별 데이터"""
    if merged_df is None or merged_df.empty or "날짜" not in merged_df.columns:
        return pd.DataFrame()
    m = merged_df[
        (merged_df["날짜"].dt.year == year) & (merged_df["날짜"].dt.month == month)
    ].copy()
    return m


def _calculate_daily_profit_loss(
    year, month, daily_sales_df, fixed_costs, variable_ratio, breakeven_daily, target_daily
):
    """일자별 손익 분석 계산. variable_ratio는 0~1 소수."""
    if daily_sales_df is None or daily_sales_df.empty or "총매출" not in daily_sales_df.columns:
        return pd.DataFrame()
    days_in_month = monthrange(year, month)[1]
    daily_fixed = fixed_costs / days_in_month if days_in_month > 0 else 0.0
    result = []
    for _, row in daily_sales_df.iterrows():
        date = row["날짜"]
        sales = float(row.get("총매출", 0) or 0)
        variable = sales * variable_ratio if variable_ratio else 0.0
        total_cost = daily_fixed + variable
        profit = sales - total_cost
        profit_rate = (profit / sales * 100) if sales > 0 else 0.0
        breakeven_ratio = (sales / breakeven_daily * 100) if breakeven_daily and breakeven_daily > 0 else 0.0
        target_ratio = (sales / target_daily * 100) if target_daily and target_daily > 0 else 0.0
        if profit > 0 and breakeven_ratio >= 100:
            grade = "🟢 양호"
        elif profit > 0:
            grade = "🟡 보통"
        else:
            grade = "🔴 위험"
        result.append({
            "날짜": date,
            "매출": sales,
            "고정비(일할)": daily_fixed,
            "변동비": variable,
            "총비용": total_cost,
            "영업이익": profit,
            "이익률": profit_rate,
            "손익분기대비": breakeven_ratio,
            "목표대비": target_ratio,
            "등급": grade,
        })
    df = pd.DataFrame(result)
    if not df.empty and "날짜" in df.columns:
        df["요일"] = pd.to_datetime(df["날짜"]).dt.day_name().map(_WEEKDAY_KR)
    return df


def _analyze_weekday_patterns(daily_profit_df):
    """요일별 패턴 분석. daily_profit_df에 요일 컬럼 필요."""
    if daily_profit_df is None or daily_profit_df.empty or "요일" not in daily_profit_df.columns:
        return pd.DataFrame()
    agg = daily_profit_df.groupby("요일").agg({
        "매출": "mean",
        "총비용": "mean",
        "영업이익": "mean",
        "이익률": "mean",
        "손익분기대비": "mean",
        "목표대비": "mean",
    }).reset_index()
    order_map = {w: i for i, w in enumerate(_WEEKDAY_ORDER)}
    agg["_ord"] = agg["요일"].map(lambda x: order_map.get(x, 99)).fillna(99).astype(int)
    agg = agg.sort_values("_ord").drop(columns=["_ord"])
    return agg


def _simulate_target_achievement(year, month, current_sales, target_sales, fixed_costs, variable_ratio):
    """목표 달성 시뮬레이션."""
    days_in_month = monthrange(year, month)[1]
    today = today_kst()
    is_current = today.year == year and today.month == month
    current_day = today.day if is_current else days_in_month
    remaining = max(0, days_in_month - current_day)
    current_day = max(1, current_day)
    daily_avg = current_sales / current_day if current_day > 0 else 0.0
    forecast_sales = current_sales + (daily_avg * remaining) if current_day > 0 else current_sales
    var = variable_ratio or 0.0
    target_var = target_sales * var if target_sales else 0.0
    target_cost = fixed_costs + target_var
    target_profit = (target_sales - target_cost) if target_sales else 0.0
    forecast_var = forecast_sales * var
    forecast_cost = fixed_costs + forecast_var
    current_trend_profit = forecast_sales - forecast_cost
    required_daily = 0.0
    if target_sales and remaining > 0 and current_sales < target_sales:
        required_daily = (target_sales - current_sales) / remaining
    req_sales = current_sales + (required_daily * remaining) if remaining > 0 else current_sales
    req_var = req_sales * var
    req_cost = fixed_costs + req_var
    required_daily_profit = req_sales - req_cost
    return {
        "target_profit": target_profit,
        "current_trend_profit": current_trend_profit,
        "required_daily_profit": required_daily_profit,
        "forecast_sales": forecast_sales,
    }


def _diagnose_sales_drop(daily_profit_df, target_daily, breakeven_daily):
    """매출 하락 원인 자동 진단."""
    insights = []
    breakeven_fail = target_fail = drop_days = 0
    worst_weekday = ""
    if daily_profit_df is None or daily_profit_df.empty:
        return {"breakeven_fail_days": 0, "target_fail_days": 0, "worst_weekday": "", "drop_days": 0, "insights": insights}
    if "손익분기대비" in daily_profit_df.columns:
        breakeven_fail = int((daily_profit_df["손익분기대비"] < 100).sum())
        if breakeven_fail > 0:
            n = len(daily_profit_df)
            pct = (breakeven_fail / n * 100) if n else 0
            insights.append(f"손익분기 미달 일수: {breakeven_fail}일 ({pct:.0f}%)")
    if "목표대비" in daily_profit_df.columns and target_daily and target_daily > 0:
        target_fail = int((daily_profit_df["목표대비"] < 100).sum())
        if target_fail > 0:
            n = len(daily_profit_df)
            pct = (target_fail / n * 100) if n else 0
            insights.append(f"목표 미달 일수: {target_fail}일 ({pct:.0f}%)")
    if "요일" in daily_profit_df.columns and "매출" in daily_profit_df.columns and target_daily and target_daily > 0:
        wd_avg = daily_profit_df.groupby("요일")["매출"].mean()
        if not wd_avg.empty:
            worst_weekday = wd_avg.idxmin()
            worst_avg = wd_avg.min()
            if worst_avg < target_daily * 0.8:
                insights.append(f"{worst_weekday} 매출이 목표 대비 낮습니다. ({int(worst_avg):,}원 vs 목표 {int(target_daily):,}원)")
    sorted_df = daily_profit_df.sort_values("날짜").copy()
    if "매출" in sorted_df.columns and len(sorted_df) >= 2:
        sorted_df["_pct"] = sorted_df["매출"].pct_change() * 100
        drop_days = int((sorted_df["_pct"] < -20).sum())
        if drop_days > 0:
            insights.append(f"급락 일수: {drop_days}일 (전일 대비 -20% 이상)")
    return {"breakeven_fail_days": breakeven_fail, "target_fail_days": target_fail, "worst_weekday": worst_weekday, "drop_days": drop_days, "insights": insights}


def _sensitivity_analysis(base_sales, fixed_costs, variable_ratio):
    """비용 구조 민감도 분석. variable_ratio 0~1."""
    scenarios = []
    var = variable_ratio or 0.0
    for change in [-20, -10, 0, 10, 20]:
        new_fixed = fixed_costs * (1 + change / 100)
        v = base_sales * var
        tc = new_fixed + v
        profit = base_sales - tc
        scenarios.append({"시나리오": f"고정비 {change:+.0f}%", "매출": base_sales, "고정비": new_fixed, "변동비": v, "총비용": tc, "영업이익": profit, "이익률": (profit / base_sales * 100) if base_sales > 0 else 0})
    for change in [-10, -5, 0, 5, 10]:
        new_var = var * (1 + change / 100)
        v = base_sales * new_var
        tc = fixed_costs + v
        profit = base_sales - tc
        scenarios.append({"시나리오": f"변동비율 {change:+.0f}%", "매출": base_sales, "고정비": fixed_costs, "변동비": v, "총비용": tc, "영업이익": profit, "이익률": (profit / base_sales * 100) if base_sales > 0 else 0})
    for change in [-30, -20, -10, 0, 10, 20, 30]:
        new_sales = base_sales * (1 + change / 100)
        v = new_sales * var
        tc = fixed_costs + v
        profit = new_sales - tc
        scenarios.append({"시나리오": f"매출 {change:+.0f}%", "매출": new_sales, "고정비": fixed_costs, "변동비": v, "총비용": tc, "영업이익": profit, "이익률": (profit / new_sales * 100) if new_sales > 0 else 0})
    return pd.DataFrame(scenarios)


def _assess_target_difficulty(year, month, current_sales, target_sales, daily_avg, required_daily):
    """목표 달성 난이도 평가."""
    days_in_month = monthrange(year, month)[1]
    today = today_kst()
    is_current = today.year == year and today.month == month
    current_day = today.day if is_current else days_in_month
    remaining = max(0, days_in_month - current_day)
    current_day = max(1, current_day)
    forecast = current_sales + (daily_avg * remaining) if current_day > 0 else current_sales
    achievement_prob = (forecast / target_sales * 100) if target_sales and target_sales > 0 else 0.0
    gap_ratio = (required_daily / daily_avg) if daily_avg and daily_avg > 0 else 0.0
    if achievement_prob >= 100:
        difficulty, insight = "쉬움", "현재 추세 유지 시 목표 달성 가능합니다."
    elif achievement_prob >= 90:
        difficulty, insight = "보통", f"목표 달성을 위해 일평균 {int(required_daily):,}원이 필요합니다. (현재 {int(daily_avg):,}원 대비 {gap_ratio:.1f}배)"
    elif achievement_prob >= 80:
        difficulty, insight = "어려움", f"목표 달성이 어려울 것으로 예상됩니다. (예상 달성률: {achievement_prob:.1f}%)"
    else:
        difficulty, insight = "매우 어려움", f"목표 달성이 매우 어려울 것으로 예상됩니다. (예상 달성률: {achievement_prob:.1f}%)"
    return {"difficulty": difficulty, "achievement_probability": achievement_prob, "gap_ratio": gap_ratio, "insight": insight}


def _generate_action_items(daily_profit_df, weekday_summary, target_sales, breakeven_daily):
    """개선 액션 아이템 제안."""
    actions = []
    if daily_profit_df is None or daily_profit_df.empty:
        return actions
    n = len(daily_profit_df)
    breakeven_fail = int((daily_profit_df["손익분기대비"] < 100).sum()) if "손익분기대비" in daily_profit_df.columns else 0
    if breakeven_fail > n * 0.3 and breakeven_daily and breakeven_daily > 0:
        actions.append({"priority": "높음", "title": "손익분기 미달 일수 감소", "description": f"손익분기 미달 일수가 {breakeven_fail}일로 많습니다. 매출 증대 또는 비용 절감이 필요합니다.", "expected_impact": f"손익분기 달성 시 월 영업이익 약 {int(breakeven_fail * breakeven_daily * 0.1):,}원 증가 예상"})
    if weekday_summary is not None and not weekday_summary.empty and "목표대비" in weekday_summary.columns and "매출" in weekday_summary.columns and target_sales and target_sales > 0:
        idx = weekday_summary["매출"].idxmin()
        worst = weekday_summary.loc[idx]
        if worst["목표대비"] < 80:
            wd = worst["요일"]
            actions.append({"priority": "중간", "title": f"{wd} 매출 증대", "description": f"{wd} 매출이 목표 대비 {worst['목표대비']:.0f}%로 낮습니다.", "expected_impact": f"{wd} 매출 10% 증가 시 월 영업이익 약 {int(worst['매출'] * 0.1 * 4):,}원 증가 예상"})
    return actions


def _render_key_metrics(store_id, year, month, merged_df, targets_df, fixed, var_ratio, breakeven, daily_profit_df):
    """ZONE A: 핵심 지표 (강화: 손익분기/목표 달성 일수, 평균 일별 영업이익, 손익분기 대비)"""
    render_section_header("핵심 지표", "📊")

    month_sales = 0.0
    try:
        month_sales = load_monthly_sales_total(store_id, year, month) or 0.0
    except Exception:
        pass

    target_sales = 0.0
    if not targets_df.empty:
        tr = targets_df[(targets_df["연도"] == year) & (targets_df["월"] == month)]
        if not tr.empty:
            target_sales = float(safe_get_value(tr, "목표매출", 0) or 0)

    days_in_month = monthrange(year, month)[1]
    today = today_kst()
    is_current = today.year == year and today.month == month
    current_day = today.day if is_current else days_in_month
    remaining = max(0, days_in_month - current_day)
    current_day = max(1, current_day)

    daily_avg = month_sales / current_day if current_day > 0 else 0.0
    required_daily = 0.0
    if target_sales > 0 and remaining > 0 and month_sales < target_sales:
        required_daily = (target_sales - month_sales) / remaining

    forecast = month_sales + (daily_avg * remaining) if current_day > 0 else month_sales
    forecast_achievement = (forecast / target_sales * 100) if target_sales > 0 else None

    prev_sales = 0.0
    if month == 1:
        py, pm = year - 1, 12
    else:
        py, pm = year, month - 1
    try:
        prev_sales = load_monthly_sales_total(store_id, py, pm) or 0.0
    except Exception:
        pass
    mom_pct = ((month_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else None

    breakeven_daily = (breakeven / days_in_month) if breakeven and days_in_month > 0 else 0.0
    target_daily = (target_sales / days_in_month) if target_sales and days_in_month > 0 else 0.0
    be_achieve = 0
    tg_achieve = 0
    avg_daily_profit = 0.0
    if daily_profit_df is not None and not daily_profit_df.empty:
        if "손익분기대비" in daily_profit_df.columns:
            be_achieve = int((daily_profit_df["손익분기대비"] >= 100).sum())
        if "목표대비" in daily_profit_df.columns:
            tg_achieve = int((daily_profit_df["목표대비"] >= 100).sum())
        if "영업이익" in daily_profit_df.columns:
            avg_daily_profit = float(daily_profit_df["영업이익"].mean())

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("이번 달 누적 매출", f"{int(month_sales):,}원" if month_sales else "—")
    with c2:
        ach = (month_sales / target_sales * 100) if target_sales > 0 else None
        if ach is not None:
            delta = f"{ach - 100:+.1f}%p" if ach != 100 else "0%p"
            st.metric("목표 대비 달성률", f"{ach:.1f}%", delta)
        else:
            st.metric("목표 대비 달성률", "—", help="목표 매출 미설정")
    with c3:
        st.metric("일평균 매출", f"{int(daily_avg):,}원" if daily_avg else "—")

    d1, d2, d3 = st.columns(3)
    with d1:
        if is_current and remaining > 0 and target_sales > 0 and month_sales < target_sales:
            st.metric("필요 일평균", f"{int(required_daily):,}원", f"남은 {remaining}일")
        else:
            sub = f"남은 {remaining}일" if is_current and remaining else ""
            val = "—"
            if target_sales > 0 and (not is_current or remaining == 0):
                val = "목표 달성 가능" if month_sales >= target_sales else "—"
            st.metric("필요 일평균", val, sub if sub else "")
    with d2:
        st.metric("예상 월 매출", f"{int(forecast):,}원" if forecast else "—")
    with d3:
        if forecast_achievement is not None:
            st.metric("예상 달성률", f"{forecast_achievement:.1f}%", "현 추세 기준")
        else:
            st.metric("예상 달성률", "—", "목표 미설정")

    if breakeven and breakeven > 0:
        be_pct = (month_sales / breakeven * 100) if month_sales else 0
        n_days = len(daily_profit_df) if daily_profit_df is not None and not daily_profit_df.empty else 0
        st.caption(f"📊 손익분기 대비 현재 매출: **{be_pct:.0f}%** · 손익분기 달성 일수: **{be_achieve}**/{n_days} · 목표 달성 일수: **{tg_achieve}**")
    if daily_profit_df is not None and not daily_profit_df.empty and "영업이익" in daily_profit_df.columns:
        st.caption(f"📈 평균 일별 영업이익: **{int(avg_daily_profit):,}원**")
    if mom_pct is not None:
        st.caption(f"📈 전월 대비: **{mom_pct:+.1f}%**")

    unofficial = count_unofficial_days_in_month(store_id, year, month)
    if unofficial > 0:
        st.warning(f"⚠️ 미마감 데이터 포함 ({unofficial}일): 누적 매출에 미마감일 매출이 포함됩니다.")


def _render_target_vs_actual(store_id, year, month, merged_df, targets_df, month_sales, target_sales, breakeven):
    """ZONE B: 목표 vs 실제 상세 (손익분기/목표 라인 차트)"""
    render_section_header("목표 vs 실제", "🎯")

    if not targets_df.empty:
        tr = targets_df[(targets_df["연도"] == year) & (targets_df["월"] == month)]
        if tr.empty:
            st.info("이번 달 목표가 없습니다. **목표 매출구조**에서 설정하세요.")
            if st.button("목표 매출구조 입력으로 이동", key="sales_analysis_go_target"):
                st.session_state["current_page"] = "목표 매출구조"
                st.rerun()
            return
    else:
        st.info("목표 매출이 설정되지 않았습니다. **목표 매출구조**에서 설정하세요.")
        if st.button("목표 매출구조 입력으로 이동", key="sales_analysis_go_target2"):
            st.session_state["current_page"] = "목표 매출구조"
            st.rerun()
        return

    if not target_sales or target_sales <= 0:
        st.info("목표 매출을 입력해주세요.")
        return

    diff = month_sales - target_sales
    ach = (month_sales / target_sales * 100) if target_sales > 0 else 0
    days_in_month = monthrange(year, month)[1]
    daily_target = target_sales / days_in_month if days_in_month > 0 else 0
    breakeven_daily = (breakeven / days_in_month) if breakeven and days_in_month > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("목표 매출", f"{int(target_sales):,}원")
    with col2:
        st.metric("실제 매출", f"{int(month_sales):,}원", f"{diff:+,.0f}원")
    with col3:
        st.metric("달성률", f"{ach:.1f}%", "목표 대비")
    with col4:
        st.metric("일평균 목표", f"{int(daily_target):,}원")

    month_data = _month_data(merged_df, year, month)
    if not month_data.empty and "총매출" in month_data.columns and "날짜" in month_data.columns:
        st.markdown("**일별 매출 추이 (이번 달) — 매출 vs 목표/손익분기 일평균**")
        chart_df = month_data.sort_values("날짜")[["날짜", "총매출"]].copy()
        chart_df = chart_df.rename(columns={"총매출": "매출"})
        chart_df["목표(일평균)"] = daily_target
        if breakeven_daily and breakeven_daily > 0:
            chart_df["손익분기(일평균)"] = breakeven_daily
        use_cols = ["매출", "목표(일평균)"]
        if breakeven_daily and breakeven_daily > 0:
            use_cols.append("손익분기(일평균)")
        st.line_chart(chart_df.set_index("날짜")[use_cols], height=280)
    else:
        st.caption("일별 매출 데이터가 없으면 차트가 표시되지 않습니다. **일일 마감**을 입력해주세요.")


def _render_daily_profit_table(daily_profit_df):
    """ZONE C: 일자별 손익 분석표"""
    render_section_header("일자별 손익 분석표", "📋")

    if daily_profit_df is None or daily_profit_df.empty:
        st.info("일별 매출 데이터가 없으면 손익표를 만들 수 없습니다. **일일 마감**을 입력해주세요.")
        return

    display_cols = ["날짜", "매출", "고정비(일할)", "변동비", "총비용", "영업이익", "이익률", "손익분기대비", "목표대비", "등급"]
    exist = [c for c in display_cols if c in daily_profit_df.columns]
    df = daily_profit_df[exist].copy()
    df["날짜"] = pd.to_datetime(df["날짜"]).dt.strftime("%Y-%m-%d")

    st.dataframe(df, use_container_width=True, hide_index=True, column_config={
        "매출": st.column_config.NumberColumn("매출", format="%d원"),
        "고정비(일할)": st.column_config.NumberColumn("고정비(일할)", format="%d원"),
        "변동비": st.column_config.NumberColumn("변동비", format="%d원"),
        "총비용": st.column_config.NumberColumn("총비용", format="%d원"),
        "영업이익": st.column_config.NumberColumn("영업이익", format="%d원"),
        "이익률": st.column_config.NumberColumn("이익률", format="%.1f%%"),
        "손익분기대비": st.column_config.NumberColumn("손익분기대비", format="%.0f%%"),
        "목표대비": st.column_config.NumberColumn("목표대비", format="%.0f%%"),
    })

    total_sales = float(daily_profit_df["매출"].sum())
    total_cost = float(daily_profit_df["총비용"].sum())
    total_profit = float(daily_profit_df["영업이익"].sum())
    n = len(daily_profit_df)
    avg_profit = total_profit / n if n > 0 else 0
    st.caption(f"**합계** 매출 {int(total_sales):,}원 · 비용 {int(total_cost):,}원 · 영업이익 {int(total_profit):,}원 · **평균 일별 영업이익** {int(avg_profit):,}원")


def _render_weekday_patterns(weekday_summary, target_daily):
    """ZONE D: 요일별 패턴 분석"""
    render_section_header("요일별 패턴 분석", "📅")

    if weekday_summary is None or weekday_summary.empty:
        st.caption("요일별 데이터가 없습니다. 일별 손익표가 있으면 표시됩니다.")
        return

    st.bar_chart(weekday_summary.set_index("요일")[["매출", "총비용", "영업이익"]], height=260)
    low_target = weekday_summary[weekday_summary["목표대비"] < 80] if target_daily and target_daily > 0 else pd.DataFrame()
    if not low_target.empty:
        for _, row in low_target.iterrows():
            st.warning(f"⚠️ **{row['요일']}** 매출이 목표 대비 **{row['목표대비']:.0f}%**로 낮습니다. (평균 {int(row['매출']):,}원 vs 목표 {int(target_daily):,}원)")


def _render_simulation(store_id, year, month, month_sales, target_sales, fixed, var_ratio):
    """ZONE F: 목표 달성 시뮬레이션"""
    render_section_header("목표 달성 시뮬레이션", "🔮")

    if not target_sales or target_sales <= 0:
        st.info("목표 매출을 설정하면 시뮬레이션 결과가 표시됩니다. **목표 매출구조**에서 설정하세요.")
        return
    sim = _simulate_target_achievement(year, month, month_sales, target_sales, fixed or 0.0, var_ratio or 0.0)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("목표 달성 시 예상 영업이익", f"{int(sim['target_profit']):,}원")
    with col2:
        st.metric("현재 추세 유지 시 예상 영업이익", f"{int(sim['current_trend_profit']):,}원")
    with col3:
        st.metric("필요 일평균 달성 시 예상 영업이익", f"{int(sim['required_daily_profit']):,}원")


def _render_sensitivity(month_sales, fixed, var_ratio):
    """ZONE G: 비용 구조 민감도 분석"""
    render_section_header("비용 구조 민감도 분석", "📐")

    base = month_sales if month_sales and month_sales > 0 else 10_000_000
    sens = _sensitivity_analysis(base, fixed or 0.0, var_ratio or 0.0)
    if sens.empty:
        st.caption("고정비·변동비가 없으면 민감도 분석을 할 수 없습니다.")
        return
    st.dataframe(sens, use_container_width=True, hide_index=True, column_config={
        "매출": st.column_config.NumberColumn("매출", format="%d원"),
        "고정비": st.column_config.NumberColumn("고정비", format="%d원"),
        "변동비": st.column_config.NumberColumn("변동비", format="%d원"),
        "총비용": st.column_config.NumberColumn("총비용", format="%d원"),
        "영업이익": st.column_config.NumberColumn("영업이익", format="%d원"),
        "이익률": st.column_config.NumberColumn("이익률", format="%.1f%%"),
    })


def _render_diagnosis(daily_profit_df, weekday_summary, target_sales, breakeven_daily, year, month, month_sales, daily_avg, required_daily):
    """ZONE H: 자동 진단 및 액션 아이템"""
    render_section_header("자동 진단 및 액션 아이템", "⚠️")

    target_daily = 0.0
    days_in_month = monthrange(year, month)[1]
    if target_sales and target_sales > 0 and days_in_month > 0:
        target_daily = target_sales / days_in_month

    diag = _diagnose_sales_drop(daily_profit_df, target_daily, breakeven_daily)
    for s in diag["insights"]:
        st.warning(s)
    if not diag["insights"]:
        st.caption("진단 결과: 특별한 이슈 없음.")

    if target_sales and target_sales > 0:
        diff = _assess_target_difficulty(year, month, month_sales, target_sales, daily_avg, required_daily)
        st.info(f"**목표 달성 난이도**: {diff['difficulty']} — {diff['insight']}")
    else:
        st.caption("목표 매출을 설정하면 난이도 평가가 표시됩니다.")

    actions = _generate_action_items(daily_profit_df, weekday_summary, target_sales, breakeven_daily)
    if actions:
        st.markdown("**개선 액션**")
        for a in actions:
            with st.expander(f"{a['priority']}: {a['title']}", expanded=(a["priority"] == "높음")):
                st.write(a["description"])
                st.caption(a["expected_impact"])
    else:
        st.success("✅ 당장 추천할 개선 액션이 없습니다. 현재 추세를 유지해 보세요.")


def _render_trends(store_id, year, month, merged_df):
    """ZONE E: 트렌드 분석 (일별 이번 달, 월간 6개월)"""
    render_section_header("트렌드 분석", "📈")

    month_data = _month_data(merged_df, year, month)
    if not month_data.empty and "총매출" in month_data.columns:
        st.markdown("**일별 매출 (이번 달)**")
        c = month_data.sort_values("날짜")[["날짜", "총매출"]].copy()
        st.line_chart(c.set_index("날짜")["총매출"], height=220)
    else:
        st.caption("이번 달 일별 데이터 없음")

    today = today_kst()
    six_months_start = today - timedelta(days=180)
    if not merged_df.empty and "날짜" in merged_df.columns and "총매출" in merged_df.columns:
        recent = merged_df[merged_df["날짜"].dt.date >= six_months_start].copy()
        if not recent.empty:
            recent["연도"] = recent["날짜"].dt.year
            recent["월"] = recent["날짜"].dt.month
            monthly = recent.groupby(["연도", "월"])["총매출"].sum().reset_index()
            monthly["월키"] = monthly["연도"].astype(str) + "-" + monthly["월"].astype(str).str.zfill(2)
            monthly = monthly.sort_values(["연도", "월"]).tail(6)
            st.markdown("**월간 트렌드 (최근 6개월)**")
            st.bar_chart(monthly.set_index("월키")["총매출"], height=220)


def _render_detailed_analysis(store_id, year, month, merged_df):
    """ZONE I: 상세 분석 (방문자, 결제수단, 예측)"""
    render_section_header("상세 분석", "🔍")

    month_data = _month_data(merged_df, year, month)
    month_sales = 0.0
    try:
        month_sales = load_monthly_sales_total(store_id, year, month) or 0.0
    except Exception:
        pass

    # 방문자 / 객단가
    if not month_data.empty and "방문자수" in month_data.columns and "총매출" in month_data.columns:
        visitors = month_data["방문자수"].sum()
        if visitors > 0:
            st.metric("총 방문자", f"{int(visitors):,}명")
            st.metric("객단가", f"{int(month_sales / visitors):,}원")
        month_sales_df = month_data[["날짜", "총매출"]].copy()
        month_visitors_df = month_data[["날짜", "방문자수"]].copy()
        try:
            corr = calculate_correlation(month_sales_df, month_visitors_df)
            if corr is not None:
                st.caption(f"매출·방문자 상관계수: **{corr:.3f}**")
        except Exception:
            pass
    else:
        st.caption("방문자 데이터가 없으면 객단가·상관계수를 계산할 수 없습니다.")

    # 결제 수단
    if not month_data.empty and ("카드매출" in month_data.columns or "현금매출" in month_data.columns):
        card = month_data["카드매출"].sum() if "카드매출" in month_data.columns else 0
        cash = month_data["현금매출"].sum() if "현금매출" in month_data.columns else 0
        total = card + cash
        if total > 0:
            st.markdown("**결제 수단**")
            st.caption(f"카드 {card / total * 100:.1f}% · 현금 {cash / total * 100:.1f}%")

    # 예측 및 액션
    days_in_month = monthrange(year, month)[1]
    today = today_kst()
    is_current = today.year == year and today.month == month
    current_day = today.day if is_current else days_in_month
    remaining = max(0, days_in_month - current_day)
    daily_avg = month_sales / current_day if current_day > 0 else 0.0
    forecast = month_sales + (daily_avg * remaining) if current_day > 0 else month_sales

    st.markdown("**예상 및 액션**")
    st.metric("현재 추세 기준 예상 월 매출", f"{int(forecast):,}원")
    if remaining > 0 and is_current:
        targets_df = load_csv("targets.csv", default_columns=["연도", "월", "목표매출"], store_id=store_id)
        target_sales = 0.0
        if not targets_df.empty:
            tr = targets_df[(targets_df["연도"] == year) & (targets_df["월"] == month)]
            if not tr.empty:
                target_sales = float(safe_get_value(tr, "목표매출", 0) or 0)
        if target_sales > 0 and month_sales < target_sales:
            need = (target_sales - month_sales) / remaining
            st.warning(f"📌 목표 달성을 위해 남은 {remaining}일 동안 **일평균 {int(need):,}원**이 필요합니다.")
        elif target_sales > 0 and month_sales >= target_sales:
            st.success("✅ 목표 달성 가능 (현재 추세 유지 시)")


def render_sales_analysis():
    """매출 분석 페이지 렌더링 (리디자인)"""
    render_page_header("매출 분석", "📊")

    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    # 상단 CTA + 새로고침
    col_cta, col_ref, _ = st.columns([2, 1, 3])
    with col_cta:
        if st.button("📉 매출 하락 원인 찾기", type="primary", use_container_width=True, key="sales_analysis_drop"):
            st.session_state["current_page"] = "매출 하락 원인 찾기"
            st.rerun()
    with col_ref:
        if st.button("🔄 매출 새로고침", key="sales_analysis_refresh", use_container_width=True):
            load_csv.clear()
            try:
                load_monthly_sales_total.clear()
            except Exception:
                pass
            st.success("매출 데이터를 새로고침했습니다.")
            st.rerun()

    st.markdown("""
    <div style="padding: 1rem; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 8px; margin-bottom: 1.5rem;">
        <p style="margin: 0; font-size: 1rem; line-height: 1.6;">
            <strong>매출은 가게의 생명줄입니다.</strong><br>
            목표를 달성하기 위해 매일 확인하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)

    year = current_year_kst()
    month = current_month_kst()

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input("연도", min_value=2020, max_value=2100, value=year, key="sales_analysis_year")
    with col2:
        selected_month = st.number_input("월", min_value=1, max_value=12, value=month, key="sales_analysis_month")

    render_section_divider()

    sales_df, merged_df = _build_sales_and_merged(store_id)
    targets_df = load_csv(
        "targets.csv",
        default_columns=["연도", "월", "목표매출", "목표원가율", "목표인건비율", "목표임대료율", "목표기타비용율", "목표순이익률"],
        store_id=store_id,
    )

    month_sales = 0.0
    try:
        month_sales = load_monthly_sales_total(store_id, selected_year, selected_month) or 0.0
    except Exception:
        pass

    target_sales = 0.0
    if not targets_df.empty:
        tr = targets_df[(targets_df["연도"] == selected_year) & (targets_df["월"] == selected_month)]
        if not tr.empty:
            target_sales = float(safe_get_value(tr, "목표매출", 0) or 0)

    if merged_df.empty and not sales_df.empty:
        merged_df = sales_df.copy()
        if "방문자수" not in merged_df.columns:
            merged_df["방문자수"] = 0

    if merged_df.empty:
        st.info("저장된 매출 데이터가 없습니다. **일일 마감**에서 매출을 입력한 뒤 분석할 수 있습니다.")
        if st.button("일일 마감 입력으로 이동", key="sales_analysis_go_daily"):
            st.session_state["current_page"] = "일일 입력(통합)"
            st.rerun()
        return

    fixed = get_fixed_costs(store_id, selected_year, selected_month) or 0.0
    var_ratio = get_variable_cost_ratio(store_id, selected_year, selected_month) or 0.0
    breakeven = calculate_break_even_sales(store_id, selected_year, selected_month) or 0.0
    days_in_month = monthrange(selected_year, selected_month)[1]
    today = today_kst()
    is_current = today.year == selected_year and today.month == selected_month
    current_day = max(1, today.day if is_current else days_in_month)
    remaining = max(0, days_in_month - current_day)
    daily_avg = month_sales / current_day if current_day > 0 else 0.0
    required_daily = (target_sales - month_sales) / remaining if target_sales and remaining > 0 and month_sales < target_sales else 0.0
    breakeven_daily = (breakeven / days_in_month) if breakeven and days_in_month > 0 else 0.0
    target_daily = (target_sales / days_in_month) if target_sales and days_in_month > 0 else 0.0

    month_data = _month_data(merged_df, selected_year, selected_month)
    daily_profit_df = _calculate_daily_profit_loss(
        selected_year, selected_month, month_data, fixed, var_ratio, breakeven_daily, target_daily
    )
    weekday_summary = _analyze_weekday_patterns(daily_profit_df) if daily_profit_df is not None and not daily_profit_df.empty else pd.DataFrame()

    _render_key_metrics(store_id, selected_year, selected_month, merged_df, targets_df, fixed, var_ratio, breakeven, daily_profit_df)
    render_section_divider()

    _render_target_vs_actual(
        store_id, selected_year, selected_month, merged_df, targets_df, month_sales, target_sales, breakeven
    )
    render_section_divider()

    _render_daily_profit_table(daily_profit_df)
    render_section_divider()

    _render_weekday_patterns(weekday_summary, target_daily)
    render_section_divider()

    _render_trends(store_id, selected_year, selected_month, merged_df)
    render_section_divider()

    _render_simulation(store_id, selected_year, selected_month, month_sales, target_sales, fixed, var_ratio)
    render_section_divider()

    _render_sensitivity(month_sales, fixed, var_ratio)
    render_section_divider()

    _render_diagnosis(daily_profit_df, weekday_summary, target_sales, breakeven_daily, selected_year, selected_month, month_sales, daily_avg, required_daily)
    render_section_divider()

    _render_detailed_analysis(store_id, selected_year, selected_month, merged_df)

    st.markdown("---")
    st.caption("💡 매출 입력·수정은 **일일 마감**에서 하세요. 목표·비용 구조는 **목표 매출구조**·**목표 비용구조**에서 하세요.")
