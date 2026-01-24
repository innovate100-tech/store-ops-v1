"""
매출 분석 페이지 (리디자인)
ZONE A: 핵심 지표 → B: 목표 vs 실제 → C: 트렌드 → D: 상세 분석
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
)
from src.analytics import merge_sales_visitors, calculate_correlation
from src.auth import get_current_store_id

bootstrap(page_title="매출 분석")


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


def _render_key_metrics(store_id, year, month, merged_df, targets_df):
    """ZONE A: 핵심 지표 6개 카드"""
    render_section_header("핵심 지표", "📊")

    month_sales = 0.0
    try:
        month_sales = load_monthly_sales_total(store_id, year, month) or 0.0
    except Exception:
        pass

    target_sales = 0.0
    target_row = pd.DataFrame()
    if not targets_df.empty:
        tr = targets_df[(targets_df["연도"] == year) & (targets_df["월"] == month)]
        if not tr.empty:
            target_row = tr
            target_sales = float(safe_get_value(tr, "목표매출", 0) or 0)

    days_in_month = monthrange(year, month)[1]
    today = today_kst()
    is_current = today.year == year and today.month == month
    current_day = today.day if is_current else days_in_month
    remaining = max(0, days_in_month - current_day)

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

    # 전월 대비 (캡션)
    if mom_pct is not None:
        st.caption(f"📈 전월 대비: **{mom_pct:+.1f}%**")

    unofficial = count_unofficial_days_in_month(store_id, year, month)
    if unofficial > 0:
        st.warning(f"⚠️ 미마감 데이터 포함 ({unofficial}일): 누적 매출에 미마감일 매출이 포함됩니다.")


def _render_target_vs_actual(store_id, year, month, merged_df, targets_df, month_sales, target_sales):
    """ZONE B: 목표 vs 실제 상세"""
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("목표 매출", f"{int(target_sales):,}원")
    with col2:
        st.metric("실제 매출", f"{int(month_sales):,}원", f"{diff:+,.0f}원")
    with col3:
        st.metric("달성률", f"{ach:.1f}%", "목표 대비")
    with col4:
        days_in_month = monthrange(year, month)[1]
        daily_target = target_sales / days_in_month if days_in_month > 0 else 0
        st.metric("일평균 목표", f"{int(daily_target):,}원")

    month_data = _month_data(merged_df, year, month)
    if not month_data.empty and "총매출" in month_data.columns and "날짜" in month_data.columns:
        st.markdown("**일별 매출 추이 (이번 달)**")
        chart_df = month_data.sort_values("날짜")[["날짜", "총매출"]].copy()
        chart_df = chart_df.rename(columns={"날짜": "날짜", "총매출": "매출"})
        st.line_chart(chart_df.set_index("날짜")["매출"], height=280)
    else:
        st.caption("일별 매출 데이터가 없으면 차트가 표시되지 않습니다. **일일 마감**을 입력해주세요.")


def _render_trends(store_id, year, month, merged_df):
    """ZONE C: 트렌드 분석 (일별 이번 달, 주간 4주, 월간 6개월)"""
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
    """ZONE D: 방문자, 결제수단, 예측, 인사이트"""
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

    _render_key_metrics(store_id, selected_year, selected_month, merged_df, targets_df)
    render_section_divider()

    _render_target_vs_actual(
        store_id, selected_year, selected_month, merged_df, targets_df, month_sales, target_sales
    )
    render_section_divider()

    _render_trends(store_id, selected_year, selected_month, merged_df)
    render_section_divider()

    _render_detailed_analysis(store_id, selected_year, selected_month, merged_df)

    st.markdown("---")
    st.caption("💡 매출 입력·수정은 **일일 마감**에서 하세요. 목표 설정은 **목표 매출구조**에서 하세요.")
