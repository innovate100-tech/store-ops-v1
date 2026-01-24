"""
재료 사용량 분석 페이지 (고도화) - v2.0
재료 사용량 트렌드, 메뉴별 기여도, 예측, 재고 연계, 효율성 분석, 내보내기 강화
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from src.ui_helpers import render_page_header, render_section_header, render_section_divider
from src.storage_supabase import load_csv
from src.analytics import calculate_ingredient_usage
from src.auth import get_current_store_id

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="재료 사용량 분석")


def _safe_float(x, default=0.0):
    try:
        v = float(x)
        return v if not np.isnan(v) else default
    except (TypeError, ValueError):
        return default


def _normalize_usage_date(usage_df):
    """usage_df에 '날짜' 컬럼 확보"""
    if usage_df is None or usage_df.empty:
        return usage_df
    u = usage_df.copy()
    if "날짜" not in u.columns and "date" in u.columns:
        u["날짜"] = pd.to_datetime(u["date"])
    elif "날짜" in u.columns:
        u["날짜"] = pd.to_datetime(u["날짜"])
    return u


def _calculate_daily_usage_trend(usage_df, days=30):
    """일별 사용량 트렌드. 출력: 날짜, 재료명, 사용량, 전일대비변화율(%), 급증/급감여부"""
    if usage_df is None or usage_df.empty:
        return pd.DataFrame(columns=["날짜", "재료명", "사용량", "전일대비변화율(%)", "급증/급감여부"])
    u = _normalize_usage_date(usage_df)
    if u.empty or "날짜" not in u.columns or "재료명" not in u.columns or "총사용량" not in u.columns:
        return pd.DataFrame(columns=["날짜", "재료명", "사용량", "전일대비변화율(%)", "급증/급감여부"])
    cutoff = u["날짜"].max() - timedelta(days=days)
    recent = u[u["날짜"] >= cutoff].copy()
    if recent.empty:
        return pd.DataFrame(columns=["날짜", "재료명", "사용량", "전일대비변화율(%)", "급증/급감여부"])
    daily = recent.groupby(["날짜", "재료명"])["총사용량"].sum().reset_index()
    daily.columns = ["날짜", "재료명", "사용량"]
    daily = daily.sort_values(["재료명", "날짜"])
    daily["전일사용량"] = daily.groupby("재료명")["사용량"].shift(1)
    daily["전일대비변화율(%)"] = np.where(
        daily["전일사용량"] > 0,
        ((daily["사용량"] - daily["전일사용량"]) / daily["전일사용량"] * 100).round(1),
        None
    )
    daily["급증/급감여부"] = np.where(
        daily["전일대비변화율(%)"] >= 50, "급증",
        np.where(daily["전일대비변화율(%)"] <= -50, "급감", None)
    )
    return daily[["날짜", "재료명", "사용량", "전일대비변화율(%)", "급증/급감여부"]].dropna(subset=["사용량"])


def _calculate_weekday_usage_pattern(usage_df):
    """요일별 사용량 패턴. 출력: 요일, 재료명, 평균사용량, 주말/평일구분, 비율(%)"""
    if usage_df is None or usage_df.empty:
        return pd.DataFrame(columns=["요일", "재료명", "평균사용량", "주말/평일구분", "비율(%)"])
    u = _normalize_usage_date(usage_df)
    if u.empty or "날짜" not in u.columns:
        return pd.DataFrame(columns=["요일", "재료명", "평균사용량", "주말/평일구분", "비율(%)"])
    u["요일"] = u["날짜"].dt.day_name()
    weekday_map = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일",
                   "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
    u["요일"] = u["요일"].map(weekday_map)
    u["주말/평일구분"] = u["요일"].apply(lambda x: "주말" if x in ["토요일", "일요일"] else "평일")
    pattern = u.groupby(["요일", "재료명", "주말/평일구분"])["총사용량"].mean().reset_index()
    pattern.columns = ["요일", "재료명", "주말/평일구분", "평균사용량"]
    total_by_ing = u.groupby("재료명")["총사용량"].sum()
    pattern["비율(%)"] = pattern.apply(
        lambda r: (r["평균사용량"] / total_by_ing.get(r["재료명"], 1) * 100).round(1) if total_by_ing.get(r["재료명"], 0) > 0 else 0,
        axis=1
    )
    return pattern


def _calculate_monthly_usage_trend(usage_df, months=6):
    """월별 사용량 트렌드. 출력: 년월, 재료명, 사용량, 전월대비변화율(%), 전년동기대비변화율(%)"""
    if usage_df is None or usage_df.empty:
        return pd.DataFrame(columns=["년월", "재료명", "사용량", "전월대비변화율(%)", "전년동기대비변화율(%)"])
    u = _normalize_usage_date(usage_df)
    if u.empty or "날짜" not in u.columns:
        return pd.DataFrame(columns=["년월", "재료명", "사용량", "전월대비변화율(%)", "전년동기대비변화율(%)"])
    u["년월"] = u["날짜"].dt.to_period("M").astype(str)
    monthly = u.groupby(["년월", "재료명"])["총사용량"].sum().reset_index()
    monthly.columns = ["년월", "재료명", "사용량"]
    monthly = monthly.sort_values(["재료명", "년월"])
    monthly["전월사용량"] = monthly.groupby("재료명")["사용량"].shift(1)
    monthly["전월대비변화율(%)"] = np.where(
        monthly["전월사용량"] > 0,
        ((monthly["사용량"] - monthly["전월사용량"]) / monthly["전월사용량"] * 100).round(1),
        None
    )
    monthly["년"] = monthly["년월"].str[:4].astype(int)
    monthly["월"] = monthly["년월"].str[5:].astype(int)
    monthly["전년동기년월"] = (monthly["년"] - 1).astype(str) + "-" + monthly["월"].astype(str).str.zfill(2)
    prev_year_dict = monthly.set_index(["재료명", "년월"])["사용량"].to_dict()
    monthly["전년동기사용량"] = monthly.apply(
        lambda r: prev_year_dict.get((r["재료명"], r["전년동기년월"]), None),
        axis=1
    )
    monthly["전년동기대비변화율(%)"] = monthly.apply(
        lambda r: ((r["사용량"] - r["전년동기사용량"]) / r["전년동기사용량"] * 100).round(1) if pd.notna(r["전년동기사용량"]) and r["전년동기사용량"] > 0 else None,
        axis=1
    )
    return monthly[["년월", "재료명", "사용량", "전월대비변화율(%)", "전년동기대비변화율(%)"]].dropna(subset=["사용량"])


def _calculate_menu_contribution_to_ingredient(usage_df, daily_sales_df, recipe_df, ingredient_name):
    """메뉴별 재료 사용량 기여도. 출력: 메뉴명, 사용량, 비율(%), 매출, 효율지수"""
    if usage_df is None or usage_df.empty or recipe_df is None or recipe_df.empty:
        return pd.DataFrame(columns=["메뉴명", "사용량", "비율(%)", "매출", "효율지수"])
    menus_using = recipe_df[recipe_df["재료명"] == ingredient_name]["메뉴명"].unique()
    if len(menus_using) == 0:
        return pd.DataFrame(columns=["메뉴명", "사용량", "비율(%)", "매출", "효율지수"])
    u = _normalize_usage_date(usage_df)
    if u.empty:
        return pd.DataFrame(columns=["메뉴명", "사용량", "비율(%)", "매출", "효율지수"])
    ds = daily_sales_df.copy()
    if "date" in ds.columns:
        ds["날짜"] = pd.to_datetime(ds["date"])
    elif "날짜" in ds.columns:
        ds["날짜"] = pd.to_datetime(ds["날짜"])
    if "menu_name" in ds.columns:
        ds["메뉴명"] = ds["menu_name"]
    elif "메뉴명" not in ds.columns:
        return pd.DataFrame(columns=["메뉴명", "사용량", "비율(%)", "매출", "효율지수"])
    if "qty" in ds.columns:
        ds["판매수량"] = ds["qty"]
    elif "quantity" in ds.columns:
        ds["판매수량"] = ds["quantity"]
    elif "판매수량" not in ds.columns:
        return pd.DataFrame(columns=["메뉴명", "사용량", "비율(%)", "매출", "효율지수"])
    merged = pd.merge(
        ds[["날짜", "메뉴명", "판매수량"]],
        recipe_df[(recipe_df["재료명"] == ingredient_name) & (recipe_df["메뉴명"].isin(menus_using))][["메뉴명", "사용량"]],
        on="메뉴명",
        how="inner"
    )
    merged["재료사용량"] = merged["판매수량"] * merged["사용량"]
    menu_usage = merged.groupby("메뉴명")["재료사용량"].sum().reset_index()
    menu_usage.columns = ["메뉴명", "사용량"]
    total = menu_usage["사용량"].sum()
    menu_usage["비율(%)"] = (menu_usage["사용량"] / total * 100).round(1) if total > 0 else 0.0
    menu_sales = ds.groupby("메뉴명")["판매수량"].sum().reset_index()
    menu_sales.columns = ["메뉴명", "판매수량"]
    menu_df = load_csv("menu_master.csv", store_id=get_current_store_id(), default_columns=["메뉴명", "판매가"])
    if not menu_df.empty and "판매가" in menu_df.columns:
        menu_sales = pd.merge(menu_sales, menu_df[["메뉴명", "판매가"]], on="메뉴명", how="left")
        menu_sales["매출"] = menu_sales["판매수량"] * menu_sales["판매가"].fillna(0)
    else:
        menu_sales["매출"] = 0.0
    result = pd.merge(menu_usage, menu_sales[["메뉴명", "매출"]], on="메뉴명", how="left")
    result["매출"] = result["매출"].fillna(0)
    result["효율지수"] = np.where(
        result["사용량"] > 0,
        (result["매출"] / result["사용량"]).round(2),
        0.0
    )
    return result.sort_values("사용량", ascending=False)


def _predict_ingredient_usage(usage_df, forecast_days=7, consider_trend=True, consider_seasonality=True):
    """재료 사용량 예측. 출력: 재료명, 예상사용량, 일평균, 예측신뢰도(%)"""
    if usage_df is None or usage_df.empty:
        return pd.DataFrame(columns=["재료명", "예상사용량", "일평균", "예측신뢰도(%)"])
    u = _normalize_usage_date(usage_df)
    if u.empty or "재료명" not in u.columns or "총사용량" not in u.columns:
        return pd.DataFrame(columns=["재료명", "예상사용량", "일평균", "예측신뢰도(%)"])
    maxd = u["날짜"].max()
    cutoff = maxd - timedelta(days=min(forecast_days * 2, 60))
    recent = u[u["날짜"] >= cutoff].copy()
    if recent.empty:
        return pd.DataFrame(columns=["재료명", "예상사용량", "일평균", "예측신뢰도(%)"])
    days_span = max(1, (recent["날짜"].max() - recent["날짜"].min()).days + 1)
    agg = recent.groupby("재료명")["총사용량"].sum().reset_index()
    agg.columns = ["재료명", "총사용량"]
    agg["일평균"] = agg["총사용량"] / days_span
    if consider_trend and len(recent) >= 4:
        mid = recent["날짜"].min() + (recent["날짜"].max() - recent["날짜"].min()) / 2
        first = recent[recent["날짜"] < mid].groupby("재료명")["총사용량"].sum()
        second = recent[recent["날짜"] >= mid].groupby("재료명")["총사용량"].sum()
        def adj(row):
            s1, s2 = first.get(row["재료명"], 0), second.get(row["재료명"], 0)
            if s1 and s2:
                t = max(-0.5, min(0.5, (s2 - s1) / s1))
                return row["일평균"] * (1 + 0.3 * t)
            return row["일평균"]
        agg["일평균"] = agg.apply(adj, axis=1)
    if consider_seasonality and len(recent) >= 7:
        u["요일"] = u["날짜"].dt.day_name()
        weekday_avg = u.groupby(["재료명", "요일"])["총사용량"].mean()
        def season_adj(row):
            ing = row["재료명"]
            recent_ing = recent[recent["재료명"] == ing]
            if not recent_ing.empty:
                recent_weekdays = recent_ing["날짜"].dt.day_name()
                weekday_values = [weekday_avg.get((ing, wd), row["일평균"]) for wd in recent_weekdays if pd.notna(weekday_avg.get((ing, wd), None))]
                if weekday_values:
                    return np.mean(weekday_values)
            return row["일평균"]
        agg["일평균"] = agg.apply(season_adj, axis=1)
    agg["예상사용량"] = (agg["일평균"] * forecast_days).round(2)
    agg["예측신뢰도(%)"] = 85.0
    return agg[["재료명", "예상사용량", "일평균", "예측신뢰도(%)"]]


def _analyze_usage_vs_inventory(usage_df, inventory_df):
    """사용량 vs 재고 상관 분석. 출력: 재료명, 현재고, 일평균사용량, 예상소진일, 사용량증가율(%), 위험도"""
    if usage_df is None or usage_df.empty or inventory_df is None or inventory_df.empty:
        return pd.DataFrame(columns=["재료명", "현재고", "일평균사용량", "예상소진일", "사용량증가율(%)", "위험도"])
    u = _normalize_usage_date(usage_df)
    if u.empty:
        return pd.DataFrame(columns=["재료명", "현재고", "일평균사용량", "예상소진일", "사용량증가율(%)", "위험도"])
    recent_7 = u[u["날짜"] >= u["날짜"].max() - timedelta(days=7)]
    recent_30 = u[u["날짜"] >= u["날짜"].max() - timedelta(days=30)]
    daily_7 = recent_7.groupby("재료명")["총사용량"].sum() / 7 if not recent_7.empty else pd.Series()
    daily_30 = recent_30.groupby("재료명")["총사용량"].sum() / 30 if not recent_30.empty else pd.Series()
    inv = inventory_df.set_index("재료명")["현재고"].to_dict()
    result = []
    for ing in daily_7.index:
        cur = _safe_float(inv.get(ing, 0))
        daily = daily_7.get(ing, 0)
        days_left = (cur / daily) if daily > 0 else None
        prev_30 = daily_30.get(ing, 0)
        increase = ((daily - prev_30) / prev_30 * 100) if prev_30 > 0 else 0.0
        if days_left and days_left < 3:
            risk = "긴급"
        elif days_left and days_left < 7:
            risk = "주의"
        else:
            risk = "정상"
        result.append({
            "재료명": ing,
            "현재고": cur,
            "일평균사용량": round(daily, 2),
            "예상소진일": round(days_left, 1) if days_left else None,
            "사용량증가율(%)": round(increase, 1),
            "위험도": risk,
        })
    return pd.DataFrame(result)


def _calculate_ingredient_efficiency(usage_df, daily_sales_df, recipe_df, menu_df):
    """재료 효율성 계산. 출력: 재료명, 총사용량, 총매출기여도, 효율지수, 효율등급"""
    if usage_df is None or usage_df.empty:
        return pd.DataFrame(columns=["재료명", "총사용량", "총매출기여도", "효율지수", "효율등급"])
    u = _normalize_usage_date(usage_df)
    if u.empty:
        return pd.DataFrame(columns=["재료명", "총사용량", "총매출기여도", "효율지수", "효율등급"])
    total_usage = u.groupby("재료명")["총사용량"].sum().reset_index()
    ds = daily_sales_df.copy()
    if "date" in ds.columns:
        ds["날짜"] = pd.to_datetime(ds["date"])
    elif "날짜" in ds.columns:
        ds["날짜"] = pd.to_datetime(ds["날짜"])
    if "menu_name" in ds.columns:
        ds["메뉴명"] = ds["menu_name"]
    elif "메뉴명" not in ds.columns:
        return total_usage.rename(columns={"총사용량": "총사용량"})
    if "qty" in ds.columns:
        ds["판매수량"] = ds["qty"]
    elif "quantity" in ds.columns:
        ds["판매수량"] = ds["quantity"]
    elif "판매수량" not in ds.columns:
        return total_usage.rename(columns={"총사용량": "총사용량"})
    if menu_df is not None and not menu_df.empty and "판매가" in menu_df.columns:
        menu_price = menu_df.set_index("메뉴명")["판매가"].to_dict()
        ds["판매가"] = ds["메뉴명"].map(lambda m: _safe_float(menu_price.get(m, 0)))
        ds["매출"] = ds["판매수량"] * ds["판매가"]
        menu_sales = ds.groupby("메뉴명")["매출"].sum()
        ing_to_menus = recipe_df.groupby("재료명")["메뉴명"].apply(list).to_dict()
        result = []
        for _, row in total_usage.iterrows():
            ing = row["재료명"]
            usage = row["총사용량"]
            menus = ing_to_menus.get(ing, [])
            sales_contrib = sum(menu_sales.get(m, 0) for m in menus)
            eff = (sales_contrib / usage) if usage > 0 else 0.0
            if eff > 1000:
                grade = "고효율"
            elif eff > 500:
                grade = "중효율"
            else:
                grade = "저효율"
            result.append({
                "재료명": ing,
                "총사용량": usage,
                "총매출기여도": sales_contrib,
                "효율지수": round(eff, 2),
                "효율등급": grade,
            })
        return pd.DataFrame(result).sort_values("효율지수", ascending=False)
    return total_usage.rename(columns={"총사용량": "총사용량"})


def render_ingredient_usage_summary():
    """재료 사용량 분석 페이지 렌더링 (고도화 v2.0)"""
    render_page_header("재료 사용량 분석 (고도화)", "📈")
    
    st.info("✨ **재료 사용량 분석 페이지가 고도화되었습니다!** 사용량 트렌드, 메뉴별 기여도, 예측, 재고 연계, 효율성 분석 기능이 추가되었습니다.")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    daily_sales_df = load_csv('daily_sales_items.csv', store_id=store_id, default_columns=['날짜', '메뉴명', '판매수량'])
    recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
    inventory_df = load_csv('inventory.csv', store_id=store_id, default_columns=['재료명', '현재고', '안전재고'])
    
    if daily_sales_df.empty or recipe_df.empty:
        st.warning("판매 내역과 레시피 데이터가 필요합니다.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📦 판매 입력으로 이동", key="go_to_sales_input", use_container_width=True):
                st.session_state["current_page"] = "판매 입력"
                st.rerun()
        with col2:
            if st.button("📝 레시피 입력으로 이동", key="go_to_recipe_input", use_container_width=True):
                st.session_state["current_page"] = "레시피 관리"
                st.rerun()
        return
    
    # 사용량 계산
    usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
    if usage_df.empty:
        st.info("재료 사용량을 계산할 데이터가 없습니다.")
        return
    
    usage_df = _normalize_usage_date(usage_df)
    
    # 고도화용 데이터 계산
    daily_trend_df = _calculate_daily_usage_trend(usage_df, days=30)
    weekday_pattern_df = _calculate_weekday_usage_pattern(usage_df)
    monthly_trend_df = _calculate_monthly_usage_trend(usage_df, months=6)
    predict_df = _predict_ingredient_usage(usage_df, forecast_days=7, consider_trend=True, consider_seasonality=True)
    usage_inv_df = _analyze_usage_vs_inventory(usage_df, inventory_df)
    efficiency_df = _calculate_ingredient_efficiency(usage_df, daily_sales_df, recipe_df, menu_df)
    
    # 기간별 집계 (기존 로직)
    usage_df['날짜'] = pd.to_datetime(usage_df['날짜'])
    min_date = usage_df['날짜'].min().date()
    max_date = usage_df['날짜'].max().date()
    
    # ============================================
    # ZONE A: 핵심 지표 (강화)
    # ============================================
    _render_zone_a_dashboard(usage_df, ingredient_df, monthly_trend_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 기간별 사용량 집계 (기존 유지 + 강화)
    # ============================================
    _render_zone_b_period_summary(usage_df, ingredient_df, min_date, max_date, monthly_trend_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 재료 사용량 트렌드
    # ============================================
    _render_zone_c_usage_trend(usage_df, daily_trend_df, weekday_pattern_df, monthly_trend_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE D: 메뉴별 재료 사용량 기여도
    # ============================================
    _render_zone_d_menu_contribution(usage_df, daily_sales_df, recipe_df, menu_df, ingredient_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE E: 재료 사용량 예측
    # ============================================
    _render_zone_e_usage_forecast(usage_df, predict_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE F: 재고 연계 분석
    # ============================================
    _render_zone_f_inventory_linkage(usage_df, inventory_df, usage_inv_df, predict_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE G: 재료 사용량 효율성 분석
    # ============================================
    _render_zone_g_efficiency_analysis(efficiency_df, usage_df, ingredient_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE H: 재료 사용량 최적화 액션
    # ============================================
    _render_zone_h_actions(monthly_trend_df, efficiency_df, usage_inv_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE I: 내보내기 & 액션 (강화)
    # ============================================
    _render_zone_i_export_actions(usage_df, daily_trend_df, weekday_pattern_df, monthly_trend_df, predict_df, usage_inv_df, store_id)


def _render_zone_a_dashboard(usage_df, ingredient_df, monthly_trend_df):
    """ZONE A: 핵심 지표 (총 사용량, 총 사용단가, 평균 일일 사용량, 변화율, 급증/급감 수)"""
    render_section_header("📊 재료 사용량 대시보드 (고도화)", "📊")
    
    if usage_df.empty:
        st.warning("사용량 데이터가 없습니다.")
        return
    
    u = _normalize_usage_date(usage_df)
    if u.empty:
        st.warning("사용량 데이터가 없습니다.")
        return
    
    # 총 사용량, 총 사용단가
    total_usage = u["총사용량"].sum()
    if not ingredient_df.empty and "단가" in ingredient_df.columns:
        u_with_price = pd.merge(u, ingredient_df[["재료명", "단가"]], on="재료명", how="left")
        u_with_price["단가"] = u_with_price["단가"].fillna(0)
        u_with_price["사용단가"] = u_with_price["총사용량"] * u_with_price["단가"]
        total_cost = u_with_price["사용단가"].sum()
    else:
        total_cost = 0.0
    
    # 평균 일일 사용량
    days_span = (u["날짜"].max() - u["날짜"].min()).days + 1
    avg_daily = total_usage / days_span if days_span > 0 else 0.0
    
    # 전월 대비 변화율
    month_change = None
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest = monthly_trend_df["년월"].max()
        latest_data = monthly_trend_df[monthly_trend_df["년월"] == latest]
        if not latest_data.empty and "전월대비변화율(%)" in latest_data.columns:
            month_change = latest_data["전월대비변화율(%)"].mean()
    
    # 사용량 급증/급감 재료 수 (전월 대비 ±20% 이상)
    surge_count = 0
    decline_count = 0
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest = monthly_trend_df[monthly_trend_df["년월"] == monthly_trend_df["년월"].max()]
        if not latest.empty and "전월대비변화율(%)" in latest.columns:
            surge_count = (latest["전월대비변화율(%)"] >= 20).sum()
            decline_count = (latest["전월대비변화율(%)"] <= -20).sum()
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("총 사용량", f"{total_usage:,.2f}")
    with c2:
        st.metric("총 사용단가", f"{int(total_cost):,}원" if total_cost else "0원")
    with c3:
        st.metric("평균 일일 사용량", f"{avg_daily:,.2f}")
    with c4:
        chg = f"{month_change:+.1f}%" if month_change is not None else "-"
        st.metric("사용량 변화율 (전월)", chg)
    with c5:
        st.metric("사용량 급증 재료", f"{surge_count}개")
    with c6:
        st.metric("사용량 급감 재료", f"{decline_count}개")


def _render_zone_b_period_summary(usage_df, ingredient_df, min_date, max_date, monthly_trend_df):
    """ZONE B: 기간별 사용량 집계 (기존 유지 + 전월 대비 변화율)"""
    render_section_header("📅 기간별 사용량 집계", "📅")
    
    st.markdown("**📅 기간 선택**")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=min_date, min_value=min_date, max_value=max_date, key="usage_start_date")
    with col2:
        end_date = st.date_input("종료일", value=max_date, min_value=min_date, max_value=max_date, key="usage_end_date")
    
    if start_date > end_date:
        st.error("⚠️ 시작일은 종료일보다 이전이어야 합니다.")
        return
    
    display_usage_df = usage_df[(usage_df['날짜'].dt.date >= start_date) & (usage_df['날짜'].dt.date <= end_date)].copy()
    
    if display_usage_df.empty:
        st.warning(f"선택한 기간({start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')})에 해당하는 데이터가 없습니다.")
        return
    
    if not ingredient_df.empty:
        display_usage_df = pd.merge(display_usage_df, ingredient_df[['재료명', '단가']], on='재료명', how='left')
        display_usage_df['단가'] = display_usage_df['단가'].fillna(0)
    else:
        display_usage_df['단가'] = 0.0
    display_usage_df['총사용단가'] = display_usage_df['총사용량'] * display_usage_df['단가']
    
    st.markdown(f"**📊 조회 기간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}**")
    
    ingredient_summary = display_usage_df.groupby('재료명')[['총사용량', '총사용단가']].sum().reset_index()
    ingredient_summary = ingredient_summary.sort_values('총사용단가', ascending=False)
    total_cost = ingredient_summary['총사용단가'].sum()
    ingredient_summary['비율(%)'] = (ingredient_summary['총사용단가'] / total_cost * 100).round(2) if total_cost > 0 else 0.0
    ingredient_summary['누적 비율(%)'] = ingredient_summary['비율(%)'].cumsum().round(2)
    
    def assign_abc_grade(cumulative_ratio):
        if cumulative_ratio <= 70:
            return 'A'
        elif cumulative_ratio <= 90:
            return 'B'
        else:
            return 'C'
    ingredient_summary['ABC 등급'] = ingredient_summary['누적 비율(%)'].apply(assign_abc_grade)
    
    # 전월 대비 변화율 추가
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest_month = monthly_trend_df["년월"].max()
        latest = monthly_trend_df[monthly_trend_df["년월"] == latest_month].set_index("재료명")["전월대비변화율(%)"].to_dict()
        ingredient_summary["전월대비변화율(%)"] = ingredient_summary["재료명"].map(lambda n: latest.get(n, None))
    
    st.markdown("**💰 사용 단가 TOP 10 재료**")
    top10_df = ingredient_summary.head(10).copy()
    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
    display_cols = ['순위', '재료명', '총사용량', '총사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']
    if "전월대비변화율(%)" in top10_df.columns:
        display_cols.append("전월대비변화율(%)")
    cfg = {
        "총사용단가": st.column_config.NumberColumn("총사용단가", format="%,.0f"),
        "비율(%)": st.column_config.NumberColumn("비율(%)", format="%.1f"),
    }
    if "전월대비변화율(%)" in top10_df.columns:
        cfg["전월대비변화율(%)"] = st.column_config.NumberColumn("전월대비변화율(%)", format="%+.1f")
    st.dataframe(top10_df[display_cols], use_container_width=True, hide_index=True, column_config=cfg)
    
    st.markdown("**📊 전체 재료 사용 단가 순위 (ABC 분석)**")
    full_ranking_df = ingredient_summary.copy()
    full_ranking_df.insert(0, '순위', range(1, len(full_ranking_df) + 1))
    cfg2 = {
        "총사용단가": st.column_config.NumberColumn("총사용단가", format="%,.0f"),
        "비율(%)": st.column_config.NumberColumn("비율(%)", format="%.1f"),
    }
    if "전월대비변화율(%)" in full_ranking_df.columns:
        cfg2["전월대비변화율(%)"] = st.column_config.NumberColumn("전월대비변화율(%)", format="%+.1f")
    st.dataframe(full_ranking_df[display_cols], use_container_width=True, hide_index=True, column_config=cfg2)
    
    abc_stats = full_ranking_df.groupby('ABC 등급').agg({
        '재료명': 'count',
        '총사용단가': 'sum',
        '비율(%)': 'sum'
    }).reset_index()
    abc_stats.columns = ['ABC 등급', '재료 수', '총 사용단가', '비율 합계(%)']
    st.markdown("**📈 ABC 등급별 통계**")
    st.dataframe(abc_stats, use_container_width=True, hide_index=True)


def _render_zone_c_usage_trend(usage_df, daily_trend_df, weekday_pattern_df, monthly_trend_df):
    """ZONE C: 재료 사용량 트렌드 (일별/요일별/월별)"""
    render_section_header("📈 재료 사용량 트렌드", "📈")
    
    if usage_df.empty:
        st.info("사용량 데이터가 없습니다.")
        return
    
    tab1, tab2, tab3 = st.tabs(["일별 추이", "요일별 패턴", "월별 트렌드"])
    
    with tab1:
        st.markdown("##### 일별 사용량 추이")
        days_sel = st.selectbox("기간 선택", [30, 60, 90], key="daily_trend_days", index=0)
        daily = _calculate_daily_usage_trend(usage_df, days=days_sel)
        if not daily.empty:
            ingredients = daily["재료명"].unique().tolist()
            if ingredients:
                ing_sel = st.selectbox("재료 선택", ingredients[:50], key="daily_trend_ing")
                daily_ing = daily[daily["재료명"] == ing_sel].sort_values("날짜")
            else:
                daily_ing = pd.DataFrame()
            if not daily_ing.empty:
                chart_df = pd.DataFrame({"날짜": daily_ing["날짜"], "사용량": daily_ing["사용량"]})
                st.line_chart(chart_df.set_index("날짜"))
                surge_days = daily_ing[daily_ing["급증/급감여부"] == "급증"]
                decline_days = daily_ing[daily_ing["급증/급감여부"] == "급감"]
                if not surge_days.empty or not decline_days.empty:
                    st.markdown("##### 사용량 급증/급감 일자")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("급증")
                        if not surge_days.empty:
                            st.dataframe(surge_days[["날짜", "사용량", "전일대비변화율(%)"]], use_container_width=True, hide_index=True)
                    with c2:
                        st.write("급감")
                        if not decline_days.empty:
                            st.dataframe(decline_days[["날짜", "사용량", "전일대비변화율(%)"]], use_container_width=True, hide_index=True)
        else:
            st.info("일별 트렌드 데이터가 없습니다.")
    
    with tab2:
        st.markdown("##### 요일별 사용량 패턴")
        if weekday_pattern_df is not None and not weekday_pattern_df.empty:
            ingredients = weekday_pattern_df["재료명"].unique().tolist()
            if ingredients:
                ing_sel = st.selectbox("재료 선택", ingredients[:50], key="weekday_ing")
                pattern_ing = weekday_pattern_df[weekday_pattern_df["재료명"] == ing_sel]
            else:
                pattern_ing = pd.DataFrame()
            if not pattern_ing.empty:
                weekday_order = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                pattern_ing["요일순서"] = pattern_ing["요일"].map(lambda x: weekday_order.index(x) if x in weekday_order else 99)
                pattern_ing = pattern_ing.sort_values("요일순서")
                chart_df = pd.DataFrame({"요일": pattern_ing["요일"], "평균사용량": pattern_ing["평균사용량"]})
                st.bar_chart(chart_df.set_index("요일"))
                weekend = pattern_ing[pattern_ing["주말/평일구분"] == "주말"]["평균사용량"].mean()
                weekday = pattern_ing[pattern_ing["주말/평일구분"] == "평일"]["평균사용량"].mean()
                if weekday > 0:
                    diff = ((weekend - weekday) / weekday * 100) if weekend else 0
                    st.metric("주말 vs 평일", f"{diff:+.1f}%", f"주말: {weekend:.2f} / 평일: {weekday:.2f}")
        else:
            st.info("요일별 패턴 데이터가 없습니다.")
    
    with tab3:
        st.markdown("##### 월별 사용량 트렌드")
        months_sel = st.selectbox("기간 선택", [6, 12], key="monthly_trend_months", index=0)
        monthly = _calculate_monthly_usage_trend(usage_df, months=months_sel)
        if not monthly.empty:
            ingredients = monthly["재료명"].unique().tolist()
            if ingredients:
                ing_sel = st.selectbox("재료 선택", ingredients[:50], key="monthly_ing")
                monthly_ing = monthly[monthly["재료명"] == ing_sel].sort_values("년월")
            else:
                monthly_ing = pd.DataFrame()
            if not monthly_ing.empty:
                chart_df = pd.DataFrame({"년월": monthly_ing["년월"], "사용량": monthly_ing["사용량"]})
                st.line_chart(chart_df.set_index("년월"))
                latest = monthly_ing.iloc[-1]
                if pd.notna(latest.get("전월대비변화율(%)")):
                    st.metric("전월 대비", f"{latest['전월대비변화율(%)']:+.1f}%")
                if pd.notna(latest.get("전년동기대비변화율(%)")):
                    st.metric("전년 동기 대비", f"{latest['전년동기대비변화율(%)']:+.1f}%")
            st.markdown("##### 전월 대비 변화율 TOP 10")
            latest_month = monthly["년월"].max()
            latest = monthly[monthly["년월"] == latest_month].sort_values("전월대비변화율(%)", ascending=False, na_last=True)
            top_change = latest.head(10)[["재료명", "사용량", "전월대비변화율(%)"]]
            st.dataframe(top_change, use_container_width=True, hide_index=True)
        else:
            st.info("월별 트렌드 데이터가 없습니다.")


def _render_zone_d_menu_contribution(usage_df, daily_sales_df, recipe_df, menu_df, ingredient_df):
    """ZONE D: 메뉴별 재료 사용량 기여도"""
    render_section_header("🍲 메뉴별 재료 사용량 기여도", "🍲")
    
    if usage_df.empty or recipe_df.empty:
        st.info("사용량 또는 레시피 데이터가 없습니다.")
        return
    
    ingredients = usage_df["재료명"].unique().tolist()
    if not ingredients:
        st.info("재료가 없습니다.")
        return
    
    ing_sel = st.selectbox("재료 선택", ingredients[:50], key="menu_contribution_ing")
    
    contribution_df = _calculate_menu_contribution_to_ingredient(usage_df, daily_sales_df, recipe_df, ing_sel)
    
    if contribution_df.empty:
        st.info(f"'{ing_sel}' 재료를 사용하는 메뉴가 없습니다.")
        return
    
    st.markdown(f"##### '{ing_sel}' 재료를 사용하는 메뉴별 기여도")
    st.dataframe(contribution_df, use_container_width=True, hide_index=True, column_config={
        "사용량": st.column_config.NumberColumn("사용량", format="%.2f"),
        "비율(%)": st.column_config.NumberColumn("비율(%)", format="%.1f"),
        "매출": st.column_config.NumberColumn("매출", format="%,.0f"),
        "효율지수": st.column_config.NumberColumn("효율지수", format="%.2f"),
    })
    
    st.markdown("##### 메뉴별 재료 사용량 효율성")
    low_eff = contribution_df[contribution_df["효율지수"] < contribution_df["효율지수"].median()]
    if not low_eff.empty:
        st.warning(f"비효율 메뉴: {', '.join(low_eff['메뉴명'].head(5).tolist())} → 레시피 최적화 검토 권장")


def _render_zone_e_usage_forecast(usage_df, predict_df):
    """ZONE E: 재료 사용량 예측"""
    render_section_header("🔮 재료 사용량 예측", "🔮")
    
    if usage_df.empty:
        st.info("사용량 데이터가 없습니다.")
        return
    
    forecast_days = st.selectbox("예측 기간 (일)", [3, 7, 14], key="forecast_days_sel", index=1)
    pred = _predict_ingredient_usage(usage_df, forecast_days=forecast_days, consider_trend=True, consider_seasonality=True)
    
    if pred.empty:
        st.info("예측 결과가 없습니다.")
        return
    
    st.dataframe(pred, use_container_width=True, hide_index=True, column_config={
        "예상사용량": st.column_config.NumberColumn("예상사용량", format="%.2f"),
        "일평균": st.column_config.NumberColumn("일평균", format="%.2f"),
        "예측신뢰도(%)": st.column_config.NumberColumn("예측신뢰도(%)", format="%.1f"),
    })
    st.caption("예상사용량 = 일평균 × 예측일수 (트렌드·계절성 반영)")


def _render_zone_f_inventory_linkage(usage_df, inventory_df, usage_inv_df, predict_df):
    """ZONE F: 재고 연계 분석"""
    render_section_header("🔗 재고 연계 분석", "🔗")
    
    if usage_df.empty:
        st.info("사용량 데이터가 없습니다.")
        return
    
    if inventory_df.empty:
        st.info("재고 데이터가 없습니다. 재고를 입력해 주세요.")
        if st.button("📦 재고 입력으로 이동", key="go_to_inventory_from_usage"):
            st.session_state["current_page"] = "재고 입력"
            st.rerun()
        return
    
    if usage_inv_df is not None and not usage_inv_df.empty:
        st.markdown("##### 사용량 vs 재고 상관 분석")
        st.dataframe(usage_inv_df, use_container_width=True, hide_index=True, column_config={
            "현재고": st.column_config.NumberColumn("현재고", format="%.2f"),
            "일평균사용량": st.column_config.NumberColumn("일평균사용량", format="%.2f"),
            "예상소진일": st.column_config.NumberColumn("예상소진일", format="%.1f"),
            "사용량증가율(%)": st.column_config.NumberColumn("사용량증가율(%)", format="%+.1f"),
        })
        
        urgent = usage_inv_df[usage_inv_df["위험도"] == "긴급"]
        if not urgent.empty:
            st.warning(f"⚠️ 긴급 재고 부족 위험: {', '.join(urgent['재료명'].head(5).tolist())}")
    
    if predict_df is not None and not predict_df.empty and not inventory_df.empty:
        st.markdown("##### 사용량 기반 발주 제안")
        inv = inventory_df.set_index("재료명")
        pred_with_inv = pd.merge(predict_df, inv[["현재고", "안전재고"]], left_on="재료명", right_index=True, how="inner")
        pred_with_inv["발주필요량"] = (pred_with_inv["예상사용량"] + pred_with_inv["안전재고"] - pred_with_inv["현재고"]).clip(lower=0)
        pred_with_inv = pred_with_inv[pred_with_inv["발주필요량"] > 0].sort_values("발주필요량", ascending=False)
        if not pred_with_inv.empty:
            st.dataframe(pred_with_inv[["재료명", "예상사용량", "현재고", "안전재고", "발주필요량"]], use_container_width=True, hide_index=True)
        else:
            st.info("발주 필요 재료가 없습니다.")


def _render_zone_g_efficiency_analysis(efficiency_df, usage_df, ingredient_df):
    """ZONE G: 재료 사용량 효율성 분석"""
    render_section_header("⚡ 재료 사용량 효율성 분석", "⚡")
    
    if efficiency_df is None or efficiency_df.empty:
        st.info("효율성 데이터를 계산할 수 없습니다. 매출 데이터가 필요합니다.")
        return
    
    st.markdown("##### 재료별 효율성 지수")
    st.dataframe(efficiency_df, use_container_width=True, hide_index=True, column_config={
        "총사용량": st.column_config.NumberColumn("총사용량", format="%.2f"),
        "총매출기여도": st.column_config.NumberColumn("총매출기여도", format="%,.0f"),
        "효율지수": st.column_config.NumberColumn("효율지수", format="%.2f"),
    })
    
    low_eff = efficiency_df[efficiency_df["효율등급"] == "저효율"]
    if not low_eff.empty:
        st.warning(f"⚠️ 저효율 재료: {', '.join(low_eff['재료명'].head(5).tolist())} → 레시피 최적화 검토 권장")


def _render_zone_h_actions(monthly_trend_df, efficiency_df, usage_inv_df):
    """ZONE H: 재료 사용량 최적화 액션"""
    render_section_header("💡 재료 사용량 최적화 액션", "💡")
    
    actions = []
    
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest = monthly_trend_df[monthly_trend_df["년월"] == monthly_trend_df["년월"].max()]
        surge = latest[latest["전월대비변화율(%)"] >= 20]
        decline = latest[latest["전월대비변화율(%)"] <= -20]
        if not surge.empty:
            actions.append(f"📈 **사용량 급증** {len(surge)}개: {', '.join(surge['재료명'].head(5).tolist())}{' …' if len(surge) > 5 else ''} → 발주량 증가 검토")
        if not decline.empty:
            actions.append(f"📉 **사용량 급감** {len(decline)}개: {', '.join(decline['재료명'].head(5).tolist())}{' …' if len(decline) > 5 else ''} → 발주량 감소 검토")
    
    if efficiency_df is not None and not efficiency_df.empty:
        low_eff = efficiency_df[efficiency_df["효율등급"] == "저효율"]
        if not low_eff.empty:
            actions.append(f"⚡ **저효율 재료** {len(low_eff)}개: {', '.join(low_eff['재료명'].head(5).tolist())} → 레시피 최적화 검토")
    
    if usage_inv_df is not None and not usage_inv_df.empty:
        urgent = usage_inv_df[usage_inv_df["위험도"] == "긴급"]
        if not urgent.empty:
            actions.append(f"⚠️ **재고 부족 위험** {len(urgent)}개: {', '.join(urgent['재료명'].head(5).tolist())} → 즉시 발주 필요")
    
    if not actions:
        st.info("현재 권장 액션이 없습니다.")
        return
    
    for a in actions:
        st.markdown(f"- {a}")


def _render_zone_i_export_actions(usage_df, daily_trend_df, weekday_pattern_df, monthly_trend_df, predict_df, usage_inv_df, store_id):
    """ZONE I: 내보내기 & 액션 (강화)"""
    render_section_header("💾 내보내기 & 액션", "💾")
    
    ts = datetime.now().strftime("%Y%m%d")
    
    def csv_download(df, cols, fname, label, key):
        if df is None or df.empty or not all(c in df.columns for c in cols if c):
            return
        sub = df[[c for c in cols if c in df.columns]]
        csv = sub.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(label=label, data=csv, file_name=fname, mime="text/csv", key=key)
    
    if not usage_df.empty:
        csv_download(usage_df, ["날짜", "재료명", "총사용량"], f"일별사용량_{ts}.csv", "📥 일별 사용량 (CSV)", "export_daily")
    
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        csv_download(monthly_trend_df, ["년월", "재료명", "사용량", "전월대비변화율(%)"], f"월별사용량트렌드_{ts}.csv", "📥 월별 사용량 트렌드 (CSV)", "export_monthly")
    
    if weekday_pattern_df is not None and not weekday_pattern_df.empty:
        csv_download(weekday_pattern_df, ["요일", "재료명", "평균사용량", "주말/평일구분"], f"요일별사용량패턴_{ts}.csv", "📥 요일별 사용량 패턴 (CSV)", "export_weekday")
    
    if predict_df is not None and not predict_df.empty:
        csv_download(predict_df, ["재료명", "예상사용량", "일평균", "예측신뢰도(%)"], f"사용량예측_{ts}.csv", "📥 사용량 예측 (CSV)", "export_predict")
    
    if usage_inv_df is not None and not usage_inv_df.empty:
        csv_download(usage_inv_df, ["재료명", "현재고", "일평균사용량", "예상소진일", "위험도"], f"사용량재고연계_{ts}.csv", "📥 사용량-재고 연계 분석 (CSV)", "export_usage_inv")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 재고 입력으로 이동", key="go_to_inventory", use_container_width=True):
            st.session_state["current_page"] = "재고 입력"
            st.rerun()
    with col2:
        if st.button("📝 레시피 입력으로 이동", key="go_to_recipe", use_container_width=True):
            st.session_state["current_page"] = "레시피 관리"
            st.rerun()


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_ingredient_usage_summary()
