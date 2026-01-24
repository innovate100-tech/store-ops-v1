"""
판매 메뉴 분석 페이지 (고도화) - v2.0
메뉴별 판매 트렌드, 포트폴리오 분석, 상관관계, 수명주기, 가격 시뮬레이션, 계절성 분석, 최적화 액션
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from src.ui_helpers import render_page_header, render_section_header, render_section_divider
from src.utils.time_utils import today_kst
from src.storage_supabase import load_csv
from src.analytics import calculate_menu_cost
from src.auth import get_current_store_id
from ui_pages.design_lab.menu_portfolio_helpers import (
    get_menu_portfolio_tags,
    get_menu_portfolio_categories,
    calculate_portfolio_balance_score,
)

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="판매 메뉴 분석")


def _safe_float(x, default=0.0):
    try:
        v = float(x)
        return v if not np.isnan(v) else default
    except (TypeError, ValueError):
        return default


def _normalize_sales_date(sales_df):
    """sales_df에 '날짜', '메뉴명', '판매수량' 컬럼 확보"""
    if sales_df is None or sales_df.empty:
        return sales_df
    s = sales_df.copy()
    if "날짜" not in s.columns and "date" in s.columns:
        s["날짜"] = pd.to_datetime(s["date"])
    elif "날짜" in s.columns:
        s["날짜"] = pd.to_datetime(s["날짜"])
    if "메뉴명" not in s.columns:
        if "menu_name" in s.columns:
            s["메뉴명"] = s["menu_name"]
        elif "name" in s.columns:
            s["메뉴명"] = s["name"]
    if "판매수량" not in s.columns:
        if "quantity" in s.columns:
            s["판매수량"] = s["quantity"]
        elif "qty" in s.columns:
            s["판매수량"] = s["qty"]
    return s


def _calculate_daily_menu_sales_trend(sales_df, days=30):
    """일별 메뉴 판매량 트렌드. 출력: 날짜, 메뉴명, 판매수량, 전일대비변화율(%), 급증/급감여부"""
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["날짜", "메뉴명", "판매수량", "전일대비변화율(%)", "급증/급감여부"])
    s = _normalize_sales_date(sales_df)
    if s.empty or "날짜" not in s.columns or "메뉴명" not in s.columns or "판매수량" not in s.columns:
        return pd.DataFrame(columns=["날짜", "메뉴명", "판매수량", "전일대비변화율(%)", "급증/급감여부"])
    cutoff = s["날짜"].max() - timedelta(days=days)
    recent = s[s["날짜"] >= cutoff].copy()
    if recent.empty:
        return pd.DataFrame(columns=["날짜", "메뉴명", "판매수량", "전일대비변화율(%)", "급증/급감여부"])
    daily = recent.groupby(["날짜", "메뉴명"])["판매수량"].sum().reset_index()
    daily = daily.sort_values(["메뉴명", "날짜"])
    daily["전일판매량"] = daily.groupby("메뉴명")["판매수량"].shift(1)
    daily["전일대비변화율(%)"] = np.where(
        daily["전일판매량"] > 0,
        ((daily["판매수량"] - daily["전일판매량"]) / daily["전일판매량"] * 100).round(1),
        None
    )
    daily["급증/급감여부"] = np.where(
        daily["전일대비변화율(%)"] >= 50, "급증",
        np.where(daily["전일대비변화율(%)"] <= -50, "급감", None)
    )
    return daily[["날짜", "메뉴명", "판매수량", "전일대비변화율(%)", "급증/급감여부"]].dropna(subset=["판매수량"])


def _calculate_weekday_menu_sales_pattern(sales_df):
    """요일별 메뉴 판매 패턴. 출력: 요일, 메뉴명, 평균판매량, 주말/평일구분, 비율(%)"""
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["요일", "메뉴명", "평균판매량", "주말/평일구분", "비율(%)"])
    s = _normalize_sales_date(sales_df)
    if s.empty or "날짜" not in s.columns:
        return pd.DataFrame(columns=["요일", "메뉴명", "평균판매량", "주말/평일구분", "비율(%)"])
    s["요일"] = s["날짜"].dt.day_name()
    weekday_map = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일",
                   "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
    s["요일"] = s["요일"].map(weekday_map)
    s["주말/평일구분"] = s["요일"].apply(lambda x: "주말" if x in ["토요일", "일요일"] else "평일")
    pattern = s.groupby(["요일", "메뉴명", "주말/평일구분"])["판매수량"].mean().reset_index()
    pattern.columns = ["요일", "메뉴명", "주말/평일구분", "평균판매량"]
    total_by_menu = s.groupby("메뉴명")["판매수량"].sum()
    pattern["비율(%)"] = pattern.apply(
        lambda r: (r["평균판매량"] / total_by_menu.get(r["메뉴명"], 1) * 100).round(1) if total_by_menu.get(r["메뉴명"], 0) > 0 else 0,
        axis=1
    )
    return pattern


def _calculate_monthly_menu_sales_trend(sales_df, months=6):
    """월별 메뉴 판매 트렌드. 출력: 년월, 메뉴명, 판매수량, 전월대비변화율(%), 전년동기대비변화율(%)"""
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["년월", "메뉴명", "판매수량", "전월대비변화율(%)", "전년동기대비변화율(%)"])
    s = _normalize_sales_date(sales_df)
    if s.empty or "날짜" not in s.columns:
        return pd.DataFrame(columns=["년월", "메뉴명", "판매수량", "전월대비변화율(%)", "전년동기대비변화율(%)"])
    s["년월"] = s["날짜"].dt.to_period("M").astype(str)
    monthly = s.groupby(["년월", "메뉴명"])["판매수량"].sum().reset_index()
    monthly.columns = ["년월", "메뉴명", "판매수량"]
    monthly = monthly.sort_values(["메뉴명", "년월"])
    monthly["전월판매량"] = monthly.groupby("메뉴명")["판매수량"].shift(1)
    monthly["전월대비변화율(%)"] = np.where(
        monthly["전월판매량"] > 0,
        ((monthly["판매수량"] - monthly["전월판매량"]) / monthly["전월판매량"] * 100).round(1),
        None
    )
    monthly["년"] = monthly["년월"].str[:4].astype(int)
    monthly["월"] = monthly["년월"].str[5:].astype(int)
    monthly["전년동기년월"] = (monthly["년"] - 1).astype(str) + "-" + monthly["월"].astype(str).str.zfill(2)
    prev_year_dict = monthly.set_index(["메뉴명", "년월"])["판매수량"].to_dict()
    monthly["전년동기판매량"] = monthly.apply(
        lambda r: prev_year_dict.get((r["메뉴명"], r["전년동기년월"]), None),
        axis=1
    )
    monthly["전년동기대비변화율(%)"] = monthly.apply(
        lambda r: ((r["판매수량"] - r["전년동기판매량"]) / r["전년동기판매량"] * 100).round(1) if pd.notna(r["전년동기판매량"]) and r["전년동기판매량"] > 0 else None,
        axis=1
    )
    return monthly[["년월", "메뉴명", "판매수량", "전월대비변화율(%)", "전년동기대비변화율(%)"]].dropna(subset=["판매수량"])


def _calculate_menu_portfolio_analysis(sales_df, menu_df, roles_dict, categories_dict):
    """메뉴 포트폴리오 분석. 출력: 구분(역할/카테고리), 항목, 판매량, 매출, 기여도(%), 균형점수"""
    if sales_df is None or sales_df.empty or menu_df.empty:
        return pd.DataFrame(columns=["구분", "항목", "판매량", "매출", "기여도(%)", "매출기여도(%)"])
    s = _normalize_sales_date(sales_df)
    if s.empty:
        return pd.DataFrame(columns=["구분", "항목", "판매량", "매출", "기여도(%)", "매출기여도(%)"])
    menu_sales = s.groupby("메뉴명")["판매수량"].sum().reset_index()
    menu_sales.columns = ["메뉴명", "판매수량"]
    if "판매가" in menu_df.columns:
        menu_sales = pd.merge(menu_sales, menu_df[["메뉴명", "판매가"]], on="메뉴명", how="left")
        menu_sales["매출"] = menu_sales["판매수량"] * menu_sales["판매가"].fillna(0)
    else:
        menu_sales["매출"] = 0.0
    total_qty = menu_sales["판매수량"].sum()
    total_rev = menu_sales["매출"].sum()
    result = []
    # 역할별
    for role in ["미끼", "볼륨", "마진", "미분류"]:
        menus = [m for m, r in roles_dict.items() if r == role]
        role_sales = menu_sales[menu_sales["메뉴명"].isin(menus)]
        qty = role_sales["판매수량"].sum()
        rev = role_sales["매출"].sum()
        qty_pct = (qty / total_qty * 100).round(1) if total_qty > 0 else 0.0
        rev_pct = (rev / total_rev * 100).round(1) if total_rev > 0 else 0.0
        result.append({"구분": "역할", "항목": role, "판매량": qty, "매출": rev, "기여도(%)": qty_pct, "매출기여도(%)": rev_pct})
    # 카테고리별
    for cat in ["대표메뉴", "주력메뉴", "유인메뉴", "보조메뉴", "기타메뉴"]:
        menus = [m for m, c in categories_dict.items() if c == cat]
        cat_sales = menu_sales[menu_sales["메뉴명"].isin(menus)]
        qty = cat_sales["판매수량"].sum()
        rev = cat_sales["매출"].sum()
        qty_pct = (qty / total_qty * 100).round(1) if total_qty > 0 else 0.0
        rev_pct = (rev / total_rev * 100).round(1) if total_rev > 0 else 0.0
        result.append({"구분": "카테고리", "항목": cat, "판매량": qty, "매출": rev, "기여도(%)": qty_pct, "매출기여도(%)": rev_pct})
    return pd.DataFrame(result)


def _calculate_menu_correlation(sales_df):
    """메뉴 간 상관관계. 출력: 메뉴A, 메뉴B, 상관계수, 상관유형"""
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["메뉴A", "메뉴B", "상관계수", "상관유형"])
    s = _normalize_sales_date(sales_df)
    if s.empty or "날짜" not in s.columns or "메뉴명" not in s.columns or "판매수량" not in s.columns:
        return pd.DataFrame(columns=["메뉴A", "메뉴B", "상관계수", "상관유형"])
    pivot = s.pivot_table(index="날짜", columns="메뉴명", values="판매수량", aggfunc="sum", fill_value=0)
    if pivot.empty or len(pivot.columns) < 2:
        return pd.DataFrame(columns=["메뉴A", "메뉴B", "상관계수", "상관유형"])
    corr = pivot.corr()
    result = []
    for i, menu_a in enumerate(corr.columns):
        for j, menu_b in enumerate(corr.columns):
            if i < j:
                coef = corr.loc[menu_a, menu_b]
                if pd.notna(coef):
                    if coef >= 0.5:
                        typ = "강한 양의 상관"
                    elif coef >= 0.3:
                        typ = "양의 상관"
                    elif coef <= -0.5:
                        typ = "강한 음의 상관"
                    elif coef <= -0.3:
                        typ = "음의 상관"
                    else:
                        typ = "약한 상관"
                    result.append({"메뉴A": menu_a, "메뉴B": menu_b, "상관계수": round(coef, 2), "상관유형": typ})
    return pd.DataFrame(result).sort_values("상관계수", ascending=False)


def _calculate_menu_lifecycle(sales_df, menu_df, new_menu_threshold_days=90):
    """메뉴 수명주기 분석. 출력: 메뉴명, 메뉴유형, 판매량추세, 성과평가"""
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["메뉴명", "메뉴유형", "판매량추세", "성과평가"])
    s = _normalize_sales_date(sales_df)
    if s.empty:
        return pd.DataFrame(columns=["메뉴명", "메뉴유형", "판매량추세", "성과평가"])
    max_date = s["날짜"].max()
    cutoff = max_date - timedelta(days=new_menu_threshold_days)
    first_sale = s.groupby("메뉴명")["날짜"].min()
    result = []
    for menu in s["메뉴명"].unique():
        menu_data = s[s["메뉴명"] == menu].sort_values("날짜")
        first = first_sale.get(menu)
        is_new = first and first >= cutoff
        menu_type = "신메뉴" if is_new else "기존메뉴"
        if len(menu_data) >= 2:
            mid = len(menu_data) // 2
            first_half = menu_data.iloc[:mid]["판매수량"].sum()
            second_half = menu_data.iloc[mid:]["판매수량"].sum()
            if first_half > 0:
                trend_pct = ((second_half - first_half) / first_half * 100)
                if trend_pct >= 10:
                    trend = "증가"
                elif trend_pct <= -10:
                    trend = "감소"
                else:
                    trend = "유지"
            else:
                trend = "유지"
        else:
            trend = "유지"
        avg_qty = menu_data["판매수량"].mean()
        if avg_qty >= 50:
            perf = "우수"
        elif avg_qty >= 20:
            perf = "보통"
        else:
            perf = "저조"
        result.append({"메뉴명": menu, "메뉴유형": menu_type, "판매량추세": trend, "성과평가": perf})
    return pd.DataFrame(result)


def _simulate_menu_price_change(menu_name, price_change_pct, sales_df, menu_df, recipe_df, ingredient_df):
    """메뉴 가격 조정 시뮬레이션. 출력: 현재가격, 조정가격, 예상판매량, 예상매출, 예상이익, 최적가격"""
    if sales_df is None or sales_df.empty or menu_df.empty:
        return {}
    s = _normalize_sales_date(sales_df)
    if s.empty:
        return {}
    menu_info = menu_df[menu_df["메뉴명"] == menu_name]
    if menu_info.empty:
        return {}
    current_price = _safe_float(menu_info.iloc[0].get("판매가", 0))
    if current_price <= 0:
        return {}
    new_price = current_price * (1 + price_change_pct / 100)
    menu_sales = s[s["메뉴명"] == menu_name]
    avg_qty = menu_sales["판매수량"].mean() if not menu_sales.empty else 0
    # 가격 탄력성 가정: 가격 +10% -> 판매량 -5% (탄력성 -0.5)
    elasticity = -0.5
    qty_change_pct = price_change_pct * elasticity
    expected_qty = avg_qty * (1 + qty_change_pct / 100)
    expected_revenue = expected_qty * new_price
    # 원가 계산
    cost = 0.0
    if not recipe_df.empty and not ingredient_df.empty:
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        menu_cost = cost_df[cost_df["메뉴명"] == menu_name]
        if not menu_cost.empty:
            cost = _safe_float(menu_cost.iloc[0].get("원가", 0))
    expected_profit = expected_revenue - (expected_qty * cost)
    # 최적 가격 (간단히: 현재 가격 기준 ±20% 범위에서 최대 이익)
    best_price = current_price
    best_profit = expected_profit
    for test_pct in [-20, -10, 0, 10, 20]:
        test_price = current_price * (1 + test_pct / 100)
        test_qty_change = test_pct * elasticity
        test_qty = avg_qty * (1 + test_qty_change / 100)
        test_rev = test_qty * test_price
        test_profit = test_rev - (test_qty * cost)
        if test_profit > best_profit:
            best_price = test_price
            best_profit = test_profit
    return {
        "현재가격": current_price,
        "조정가격": new_price,
        "예상판매량": round(expected_qty, 1),
        "예상매출": round(expected_revenue, 0),
        "예상이익": round(expected_profit, 0),
        "최적가격": round(best_price, 0),
    }


def _calculate_menu_seasonality(sales_df):
    """계절성 분석. 출력: 메뉴명, 월별판매량, 계절별판매량, 계절성지수"""
    if sales_df is None or sales_df.empty:
        return pd.DataFrame(columns=["메뉴명", "월별판매량", "계절별판매량", "계절성지수"])
    s = _normalize_sales_date(sales_df)
    if s.empty:
        return pd.DataFrame(columns=["메뉴명", "월별판매량", "계절별판매량", "계절성지수"])
    s["월"] = s["날짜"].dt.month
    s["계절"] = s["월"].apply(lambda m: "봄" if m in [3,4,5] else ("여름" if m in [6,7,8] else ("가을" if m in [9,10,11] else "겨울")))
    monthly = s.groupby(["메뉴명", "월"])["판매수량"].sum().reset_index()
    seasonal = s.groupby(["메뉴명", "계절"])["판매수량"].sum().reset_index()
    result = []
    for menu in s["메뉴명"].unique():
        menu_monthly = monthly[monthly["메뉴명"] == menu]["판매수량"]
        menu_seasonal = seasonal[seasonal["메뉴명"] == menu]["판매수량"]
        monthly_std = menu_monthly.std() if len(menu_monthly) > 0 else 0
        monthly_mean = menu_monthly.mean() if len(menu_monthly) > 0 else 1
        seasonality_idx = (monthly_std / monthly_mean * 100).round(1) if monthly_mean > 0 else 0.0
        result.append({
            "메뉴명": menu,
            "월별판매량": menu_monthly.sum(),
            "계절별판매량": menu_seasonal.sum(),
            "계절성지수": seasonality_idx,
        })
    return pd.DataFrame(result)


def render_sales_analysis():
    """판매 메뉴 분석 페이지 렌더링 (고도화 v2.0)"""
    render_page_header("판매 메뉴 분석 (고도화)", "📦")
    
    st.info("✨ **판매 메뉴 분석 페이지가 고도화되었습니다!** 메뉴별 판매 트렌드, 포트폴리오 분석, 상관관계, 수명주기, 가격 시뮬레이션, 계절성 분석 기능이 추가되었습니다.")
    
    # 매출 하락 원인 찾기 버튼 (상단 CTA)
    if st.button("📉 매출 하락 원인 찾기", type="primary", use_container_width=True, key="sales_analysis_btn_sales_drop"):
        st.session_state["current_page"] = "매출 하락 원인 찾기"
        st.rerun()
    
    st.markdown("---")
    
    # store_id 확인
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    
    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 판매 데이터 새로고침", key="sales_analysis_refresh", use_container_width=True):
            load_csv.clear()
            st.success("✅ 판매 데이터를 새로고침했습니다.")
            st.rerun()
    
    # 데이터 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'], store_id=store_id)
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'], store_id=store_id)
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'], store_id=store_id)
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'], store_id=store_id)
    
    if daily_sales_df.empty or menu_df.empty:
        st.warning("판매 분석을 위해서는 메뉴와 일일 판매 데이터가 필요합니다.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📦 판매 입력으로 이동", key="go_to_sales_input", use_container_width=True):
                st.session_state["current_page"] = "판매 입력"
                st.rerun()
        with col2:
            if st.button("📝 메뉴 입력으로 이동", key="go_to_menu_input", use_container_width=True):
                st.session_state["current_page"] = "판매 메뉴 입력"
                st.rerun()
        return
    
    # 날짜 정규화
    daily_sales_df = _normalize_sales_date(daily_sales_df)
    daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
    
    # 사용 가능한 날짜 범위
    min_date = daily_sales_df['날짜'].min().date()
    data_max_date = daily_sales_df['날짜'].max().date()
    today_date = today_kst()
    max_date = max(data_max_date, today_date)
    
    # 기간 선택 필터
    st.markdown("**📅 분석 기간 선택**")
    col1, col2 = st.columns(2)
    with col1:
        analysis_start_date = st.date_input("시작일", value=min_date, min_value=min_date, max_value=max_date, key="sales_mgmt_start_date")
    with col2:
        analysis_end_date = st.date_input("종료일", value=max_date, min_value=min_date, max_value=max_date, key="sales_analysis_sales_mgmt_end_date")
    
    if analysis_start_date > analysis_end_date:
        st.error("⚠️ 시작일은 종료일보다 이전이어야 합니다.")
        return
    
    # 기간 필터링
    filtered_sales_df = daily_sales_df[
        (daily_sales_df['날짜'].dt.date >= analysis_start_date) & 
        (daily_sales_df['날짜'].dt.date <= analysis_end_date)
    ].copy()
    
    if filtered_sales_df.empty:
        st.warning(f"선택한 기간({analysis_start_date.strftime('%Y년 %m월 %d일')} ~ {analysis_end_date.strftime('%Y년 %m월 %d일')})에 해당하는 판매 데이터가 없습니다.")
        return
    
    # 메뉴별 집계 및 원가 계산
    sales_summary = filtered_sales_df.groupby('메뉴명')['판매수량'].sum().reset_index()
    summary_df = pd.merge(sales_summary, menu_df[['메뉴명', '판매가']], on='메뉴명', how='left')
    summary_df['매출'] = summary_df['판매수량'] * summary_df['판매가'].fillna(0)
    
    if not recipe_df.empty and not ingredient_df.empty:
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        summary_df = pd.merge(summary_df, cost_df[['메뉴명', '원가']], on='메뉴명', how='left')
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
    
    # 고도화용 데이터 계산
    daily_trend_df = _calculate_daily_menu_sales_trend(filtered_sales_df, days=30)
    weekday_pattern_df = _calculate_weekday_menu_sales_pattern(filtered_sales_df)
    monthly_trend_df = _calculate_monthly_menu_sales_trend(filtered_sales_df, months=6)
    roles_dict = get_menu_portfolio_tags(store_id)
    categories_dict = get_menu_portfolio_categories(store_id)
    portfolio_df = _calculate_menu_portfolio_analysis(filtered_sales_df, menu_df, roles_dict, categories_dict)
    correlation_df = _calculate_menu_correlation(filtered_sales_df)
    lifecycle_df = _calculate_menu_lifecycle(filtered_sales_df, menu_df, new_menu_threshold_days=90)
    seasonality_df = _calculate_menu_seasonality(filtered_sales_df)
    
    # ============================================
    # ZONE A: 핵심 지표 (강화)
    # ============================================
    _render_zone_a_dashboard(filtered_sales_df, summary_df, monthly_trend_df, roles_dict, categories_dict, menu_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 기간별 판매량 집계 (기존 유지 + 강화)
    # ============================================
    _render_zone_b_period_summary(filtered_sales_df, summary_df, menu_df, monthly_trend_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 메뉴별 판매 트렌드
    # ============================================
    _render_zone_c_sales_trend(filtered_sales_df, daily_trend_df, weekday_pattern_df, monthly_trend_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE D: 메뉴 포트폴리오 분석
    # ============================================
    _render_zone_d_portfolio_analysis(portfolio_df, roles_dict, categories_dict, menu_df, summary_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE E: 메뉴 간 상관관계 분석
    # ============================================
    _render_zone_e_correlation(correlation_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE F: 메뉴 수명주기 분석
    # ============================================
    _render_zone_f_lifecycle(lifecycle_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE G: 메뉴 수익성 심화 분석
    # ============================================
    _render_zone_g_profitability(summary_df, menu_df, filtered_sales_df, recipe_df, ingredient_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE H: 계절성 분석
    # ============================================
    _render_zone_h_seasonality(seasonality_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE I: 메뉴 최적화 액션
    # ============================================
    _render_zone_i_actions(monthly_trend_df, summary_df, portfolio_df, lifecycle_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE J: 내보내기 & 액션 (강화)
    # ============================================
    _render_zone_j_export_actions(filtered_sales_df, daily_trend_df, weekday_pattern_df, monthly_trend_df, portfolio_df, correlation_df, store_id)


def _render_zone_a_dashboard(sales_df, summary_df, monthly_trend_df, roles_dict, categories_dict, menu_df):
    """ZONE A: 핵심 지표 (총 판매량, 총 매출, 총 이익, 평균 일일 판매량, 변화율, 급증/급감 수, 포트폴리오 균형 점수)"""
    render_section_header("📊 판매 메뉴 대시보드 (고도화)", "📊")
    
    if sales_df.empty or summary_df.empty:
        st.warning("판매 데이터가 없습니다.")
        return
    
    s = _normalize_sales_date(sales_df)
    if s.empty:
        st.warning("판매 데이터가 없습니다.")
        return
    
    total_quantity = summary_df['판매수량'].sum()
    total_revenue = summary_df['매출'].sum()
    total_profit = summary_df['이익'].sum() if '이익' in summary_df.columns else 0.0
    days_span = (s["날짜"].max() - s["날짜"].min()).days + 1
    avg_daily = total_quantity / days_span if days_span > 0 else 0.0
    
    # 전월 대비 변화율
    month_change = None
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest = monthly_trend_df["년월"].max()
        latest_data = monthly_trend_df[monthly_trend_df["년월"] == latest]
        if not latest_data.empty and "전월대비변화율(%)" in latest_data.columns:
            month_change = latest_data["전월대비변화율(%)"].mean()
    
    # 판매량 급증/급감 메뉴 수 (전월 대비 ±20% 이상)
    surge_count = 0
    decline_count = 0
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest = monthly_trend_df[monthly_trend_df["년월"] == monthly_trend_df["년월"].max()]
        if not latest.empty and "전월대비변화율(%)" in latest.columns:
            surge_count = (latest["전월대비변화율(%)"] >= 20).sum()
            decline_count = (latest["전월대비변화율(%)"] <= -20).sum()
    
    # 포트폴리오 균형 점수
    balance_score, balance_status = calculate_portfolio_balance_score(menu_df, roles_dict, categories_dict)
    
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
    with c1:
        st.metric("총 판매량", f"{int(total_quantity):,}개")
    with c2:
        st.metric("총 매출", f"{int(total_revenue):,}원")
    with c3:
        st.metric("총 이익", f"{int(total_profit):,}원")
    with c4:
        st.metric("평균 일일 판매량", f"{avg_daily:,.1f}개")
    with c5:
        chg = f"{month_change:+.1f}%" if month_change is not None else "-"
        st.metric("판매량 변화율 (전월)", chg)
    with c6:
        st.metric("판매량 급증 메뉴", f"{surge_count}개")
    with c7:
        st.metric("판매량 급감 메뉴", f"{decline_count}개")
    with c8:
        st.metric("포트폴리오 균형", f"{balance_score}점", balance_status)


def _render_zone_b_period_summary(sales_df, summary_df, menu_df, monthly_trend_df):
    """ZONE B: 기간별 판매량 집계 (기존 유지 + 전월 대비 변화율)"""
    render_section_header("📅 기간별 판매량 집계", "📅")
    
    if summary_df.empty:
        st.warning("집계 데이터가 없습니다.")
        return
    
    total_revenue = summary_df['매출'].sum()
    if total_revenue <= 0:
        st.info("매출 데이터가 충분하지 않아 ABC 분석을 할 수 없습니다.")
        return
    
    # ABC 분석 (복사본 사용)
    display_df = summary_df.copy()
    display_df = display_df.sort_values('매출', ascending=False)
    display_df['비율(%)'] = (display_df['매출'] / total_revenue * 100).round(2)
    display_df['누계 비율(%)'] = display_df['비율(%)'].cumsum().round(2)
    
    def assign_abc_grade(cumulative_ratio):
        if cumulative_ratio <= 70:
            return 'A'
        elif cumulative_ratio <= 90:
            return 'B'
        else:
            return 'C'
    display_df['ABC 등급'] = display_df['누계 비율(%)'].apply(assign_abc_grade)
    
    # 전월 대비 변화율 추가
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest_month = monthly_trend_df["년월"].max()
        latest = monthly_trend_df[monthly_trend_df["년월"] == latest_month].set_index("메뉴명")["전월대비변화율(%)"].to_dict()
        display_df["전월대비변화율(%)"] = display_df["메뉴명"].map(lambda n: latest.get(n, None))
    
    st.markdown("**📊 판매 ABC 분석**")
    display_cols = ['메뉴명', '판매수량', '매출', '비율(%)', '누계 비율(%)', 'ABC 등급']
    if "전월대비변화율(%)" in display_df.columns:
        display_cols.append("전월대비변화율(%)")
    st.dataframe(display_df[display_cols], use_container_width=True, hide_index=True, column_config={
        "매출": st.column_config.NumberColumn("매출", format="%,.0f"),
        "비율(%)": st.column_config.NumberColumn("비율(%)", format="%.1f"),
        "전월대비변화율(%)": st.column_config.NumberColumn("전월대비변화율(%)", format="%+.1f"),
    })
    
    st.markdown("**🏆 인기 메뉴 TOP 10**")
    top10_df = display_df.head(10).copy()
    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
    st.dataframe(top10_df[['순위'] + display_cols], use_container_width=True, hide_index=True, column_config={
        "매출": st.column_config.NumberColumn("매출", format="%,.0f"),
        "비율(%)": st.column_config.NumberColumn("비율(%)", format="%.1f"),
        "전월대비변화율(%)": st.column_config.NumberColumn("전월대비변화율(%)", format="%+.1f"),
    })


def _render_zone_c_sales_trend(sales_df, daily_trend_df, weekday_pattern_df, monthly_trend_df):
    """ZONE C: 메뉴별 판매 트렌드 (일별/요일별/월별)"""
    render_section_header("📈 메뉴별 판매 트렌드", "📈")
    
    if sales_df.empty:
        st.info("판매 데이터가 없습니다.")
        return
    
    tab1, tab2, tab3 = st.tabs(["일별 추이", "요일별 패턴", "월별 트렌드"])
    
    with tab1:
        st.markdown("##### 일별 메뉴 판매량 추이")
        days_sel = st.selectbox("기간 선택", [30, 60, 90], key="daily_menu_trend_days", index=0)
        daily = _calculate_daily_menu_sales_trend(sales_df, days=days_sel)
        if not daily.empty:
            ingredients = daily["메뉴명"].unique().tolist()
            if ingredients:
                menu_sel = st.selectbox("메뉴 선택", ingredients[:50], key="daily_menu_trend_menu")
                daily_menu = daily[daily["메뉴명"] == menu_sel].sort_values("날짜")
                if not daily_menu.empty:
                    chart_df = pd.DataFrame({"날짜": daily_menu["날짜"], "판매수량": daily_menu["판매수량"]})
                    st.line_chart(chart_df.set_index("날짜"))
                    surge_days = daily_menu[daily_menu["급증/급감여부"] == "급증"]
                    decline_days = daily_menu[daily_menu["급증/급감여부"] == "급감"]
                    if not surge_days.empty or not decline_days.empty:
                        st.markdown("##### 판매량 급증/급감 일자")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write("급증")
                            if not surge_days.empty:
                                st.dataframe(surge_days[["날짜", "판매수량", "전일대비변화율(%)"]], use_container_width=True, hide_index=True)
                        with c2:
                            st.write("급감")
                            if not decline_days.empty:
                                st.dataframe(decline_days[["날짜", "판매수량", "전일대비변화율(%)"]], use_container_width=True, hide_index=True)
        else:
            st.info("일별 트렌드 데이터가 없습니다.")
    
    with tab2:
        st.markdown("##### 요일별 메뉴 판매 패턴")
        if weekday_pattern_df is not None and not weekday_pattern_df.empty:
            ingredients = weekday_pattern_df["메뉴명"].unique().tolist()
            if ingredients:
                menu_sel = st.selectbox("메뉴 선택", ingredients[:50], key="weekday_menu")
                pattern_menu = weekday_pattern_df[weekday_pattern_df["메뉴명"] == menu_sel]
                if not pattern_menu.empty:
                    weekday_order = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                    pattern_menu["요일순서"] = pattern_menu["요일"].map(lambda x: weekday_order.index(x) if x in weekday_order else 99)
                    pattern_menu = pattern_menu.sort_values("요일순서")
                    chart_df = pd.DataFrame({"요일": pattern_menu["요일"], "평균판매량": pattern_menu["평균판매량"]})
                    st.bar_chart(chart_df.set_index("요일"))
                    weekend = pattern_menu[pattern_menu["주말/평일구분"] == "주말"]["평균판매량"].mean()
                    weekday = pattern_menu[pattern_menu["주말/평일구분"] == "평일"]["평균판매량"].mean()
                    if weekday > 0:
                        diff = ((weekend - weekday) / weekday * 100) if weekend else 0
                        st.metric("주말 vs 평일", f"{diff:+.1f}%", f"주말: {weekend:.2f} / 평일: {weekday:.2f}")
        else:
            st.info("요일별 패턴 데이터가 없습니다.")
        
        # 요일별 인기 메뉴 TOP 3
        st.markdown("##### 요일별 인기 메뉴 TOP 3")
        s = _normalize_sales_date(sales_df)
        if not s.empty and "날짜" in s.columns:
            s["요일"] = s["날짜"].dt.day_name()
            day_names_kr = {
                'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
                'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
            }
            s["요일한글"] = s["요일"].map(day_names_kr)
            day_menu_summary = s.groupby(['요일한글', '메뉴명'])['판매수량'].sum().reset_index()
            day_menu_summary = day_menu_summary.sort_values(['요일한글', '판매수량'], ascending=[True, False])
            day_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
            for day in day_order:
                day_data = day_menu_summary[day_menu_summary['요일한글'] == day].head(3)
                if not day_data.empty:
                    st.write(f"**{day} TOP 3**")
                    st.dataframe(day_data[['메뉴명', '판매수량']], use_container_width=True, hide_index=True, column_config={
                        "판매수량": st.column_config.NumberColumn("판매수량", format="%,.0f"),
                    })
    
    with tab3:
        st.markdown("##### 월별 메뉴 판매 트렌드")
        months_sel = st.selectbox("기간 선택", [6, 12], key="monthly_menu_trend_months", index=0)
        monthly = _calculate_monthly_menu_sales_trend(sales_df, months=months_sel)
        if not monthly.empty:
            ingredients = monthly["메뉴명"].unique().tolist()
            if ingredients:
                menu_sel = st.selectbox("메뉴 선택", ingredients[:50], key="monthly_menu")
                monthly_menu = monthly[monthly["메뉴명"] == menu_sel].sort_values("년월")
                if not monthly_menu.empty:
                    chart_df = pd.DataFrame({"년월": monthly_menu["년월"], "판매수량": monthly_menu["판매수량"]})
                    st.line_chart(chart_df.set_index("년월"))
                    latest = monthly_menu.iloc[-1]
                    if pd.notna(latest.get("전월대비변화율(%)")):
                        st.metric("전월 대비", f"{latest['전월대비변화율(%)']:+.1f}%")
                    if pd.notna(latest.get("전년동기대비변화율(%)")):
                        st.metric("전년 동기 대비", f"{latest['전년동기대비변화율(%)']:+.1f}%")
            st.markdown("##### 전월 대비 변화율 TOP 10")
            latest_month = monthly["년월"].max()
            latest = monthly[monthly["년월"] == latest_month].sort_values("전월대비변화율(%)", ascending=False, na_last=True)
            top_change = latest.head(10)[["메뉴명", "판매수량", "전월대비변화율(%)"]]
            st.dataframe(top_change, use_container_width=True, hide_index=True)
        else:
            st.info("월별 트렌드 데이터가 없습니다.")


def _render_zone_d_portfolio_analysis(portfolio_df, roles_dict, categories_dict, menu_df, summary_df):
    """ZONE D: 메뉴 포트폴리오 분석"""
    render_section_header("🎯 메뉴 포트폴리오 분석", "🎯")
    
    if portfolio_df.empty:
        st.info("포트폴리오 분석 데이터가 없습니다.")
        return
    
    tab1, tab2 = st.tabs(["역할별 기여도", "카테고리별 기여도"])
    
    with tab1:
        st.markdown("##### 역할별 메뉴 기여도")
        role_df = portfolio_df[portfolio_df["구분"] == "역할"]
        if not role_df.empty:
            st.dataframe(role_df, use_container_width=True, hide_index=True, column_config={
                "판매량": st.column_config.NumberColumn("판매량", format="%,.0f"),
                "매출": st.column_config.NumberColumn("매출", format="%,.0f"),
                "기여도(%)": st.column_config.NumberColumn("기여도(%)", format="%.1f"),
                "매출기여도(%)": st.column_config.NumberColumn("매출기여도(%)", format="%.1f"),
            })
            st.bar_chart(role_df.set_index("항목")[["기여도(%)", "매출기여도(%)"]])
        else:
            st.info("역할별 데이터가 없습니다.")
    
    with tab2:
        st.markdown("##### 카테고리별 메뉴 기여도")
        cat_df = portfolio_df[portfolio_df["구분"] == "카테고리"]
        if not cat_df.empty:
            st.dataframe(cat_df, use_container_width=True, hide_index=True, column_config={
                "판매량": st.column_config.NumberColumn("판매량", format="%,.0f"),
                "매출": st.column_config.NumberColumn("매출", format="%,.0f"),
                "기여도(%)": st.column_config.NumberColumn("기여도(%)", format="%.1f"),
                "매출기여도(%)": st.column_config.NumberColumn("매출기여도(%)", format="%.1f"),
            })
            st.bar_chart(cat_df.set_index("항목")[["기여도(%)", "매출기여도(%)"]])
        else:
            st.info("카테고리별 데이터가 없습니다.")
    
    # 포트폴리오 균형도
    balance_score, balance_status = calculate_portfolio_balance_score(menu_df, roles_dict, categories_dict)
    st.markdown("##### 포트폴리오 균형도")
    st.metric("종합 균형 점수", f"{balance_score}점", balance_status)


def _render_zone_e_correlation(correlation_df):
    """ZONE E: 메뉴 간 상관관계 분석"""
    render_section_header("🔗 메뉴 간 상관관계 분석", "🔗")
    
    if correlation_df.empty:
        st.info("상관관계 분석 데이터가 없습니다. (메뉴가 2개 이상 필요합니다)")
        return
    
    st.markdown("##### 메뉴 간 판매 상관관계")
    strong_positive = correlation_df[correlation_df["상관계수"] >= 0.5]
    strong_negative = correlation_df[correlation_df["상관계수"] <= -0.5]
    
    if not strong_positive.empty:
        st.markdown("**강한 양의 상관 메뉴 조합 (세트 메뉴 추천)**")
        st.dataframe(strong_positive[["메뉴A", "메뉴B", "상관계수", "상관유형"]], use_container_width=True, hide_index=True)
    
    if not strong_negative.empty:
        st.markdown("**강한 음의 상관 메뉴 조합 (대체 메뉴)**")
        st.dataframe(strong_negative[["메뉴A", "메뉴B", "상관계수", "상관유형"]], use_container_width=True, hide_index=True)
    
    st.markdown("##### 전체 상관관계 매트릭스 (TOP 20)")
    top_corr = correlation_df.head(20)
    st.dataframe(top_corr, use_container_width=True, hide_index=True)


def _render_zone_f_lifecycle(lifecycle_df):
    """ZONE F: 메뉴 수명주기 분석"""
    render_section_header("🔄 메뉴 수명주기 분석", "🔄")
    
    if lifecycle_df.empty:
        st.info("수명주기 분석 데이터가 없습니다.")
        return
    
    tab1, tab2 = st.tabs(["신메뉴 성과", "기존 메뉴 추세"])
    
    with tab1:
        st.markdown("##### 신메뉴 성과 분석")
        new_menus = lifecycle_df[lifecycle_df["메뉴유형"] == "신메뉴"]
        if not new_menus.empty:
            st.dataframe(new_menus, use_container_width=True, hide_index=True)
        else:
            st.info("신메뉴가 없습니다.")
    
    with tab2:
        st.markdown("##### 기존 메뉴 판매 추세")
        existing = lifecycle_df[lifecycle_df["메뉴유형"] == "기존메뉴"]
        if not existing.empty:
            declining = existing[existing["판매량추세"] == "감소"]
            increasing = existing[existing["판매량추세"] == "증가"]
            if not declining.empty:
                st.warning(f"⚠️ 판매량 감소 메뉴: {', '.join(declining['메뉴명'].head(5).tolist())} → 리뉴얼 검토 권장")
            if not increasing.empty:
                st.success(f"✅ 판매량 증가 메뉴: {', '.join(increasing['메뉴명'].head(5).tolist())} → 주력 메뉴 승격 검토")
            st.dataframe(existing, use_container_width=True, hide_index=True)
        else:
            st.info("기존 메뉴 데이터가 없습니다.")


def _render_zone_g_profitability(summary_df, menu_df, sales_df, recipe_df, ingredient_df):
    """ZONE G: 메뉴 수익성 심화 분석"""
    render_section_header("💰 메뉴 수익성 심화 분석", "💰")
    
    if summary_df.empty:
        st.warning("수익성 데이터가 없습니다.")
        return
    
    tab1, tab2, tab3 = st.tabs(["수익성 분석", "수익성 지수", "가격 조정 시뮬레이션"])
    
    with tab1:
        st.markdown("##### 수익성 분석")
        if '이익률' in summary_df.columns:
            profitability_df = summary_df.sort_values('이익률', ascending=False).copy()
            col1, col2 = st.columns(2)
            with col1:
                st.write("**✅ 최고 수익성 메뉴 (이익률 기준)**")
                top_profit_df = profitability_df.head(5).copy()
                st.dataframe(top_profit_df[['메뉴명', '이익', '이익률', '원가율']], use_container_width=True, hide_index=True, column_config={
                    "이익": st.column_config.NumberColumn("이익", format="%,.0f"),
                    "이익률": st.column_config.NumberColumn("이익률", format="%.1f"),
                    "원가율": st.column_config.NumberColumn("원가율", format="%.1f"),
                })
            with col2:
                st.write("**⚠️ 저수익성 메뉴 (이익률 기준)**")
                low_profit_df = profitability_df[profitability_df['이익률'] < 30].copy()
                if not low_profit_df.empty:
                    st.dataframe(low_profit_df.head(5)[['메뉴명', '이익', '이익률', '원가율']], use_container_width=True, hide_index=True, column_config={
                        "이익": st.column_config.NumberColumn("이익", format="%,.0f"),
                        "이익률": st.column_config.NumberColumn("이익률", format="%.1f"),
                        "원가율": st.column_config.NumberColumn("원가율", format="%.1f"),
                    })
                else:
                    st.info("저수익성 메뉴가 없습니다.")
        else:
            st.info("이익률 데이터가 없습니다.")
    
    with tab2:
        st.markdown("##### 메뉴별 수익성 지수")
        if '이익' in summary_df.columns and '판매수량' in summary_df.columns:
            summary_df['수익성지수'] = np.where(
                summary_df['판매수량'] > 0,
                (summary_df['이익'] / summary_df['판매수량']).round(2),
                0.0
            )
            summary_df = summary_df.sort_values('수익성지수', ascending=False)
            st.dataframe(summary_df[['메뉴명', '판매수량', '이익', '수익성지수', '이익률']], use_container_width=True, hide_index=True, column_config={
                "이익": st.column_config.NumberColumn("이익", format="%,.0f"),
                "수익성지수": st.column_config.NumberColumn("수익성지수", format="%.2f"),
                "이익률": st.column_config.NumberColumn("이익률", format="%.1f"),
            })
        else:
            st.info("이익 데이터가 없습니다.")
    
    with tab3:
        st.markdown("##### 메뉴 가격 조정 시뮬레이션")
        menus = summary_df['메뉴명'].unique().tolist()
        if menus:
            menu_sel = st.selectbox("메뉴 선택", menus[:50], key="price_sim_menu")
            price_change = st.slider("가격 변화율 (%)", -20, 20, 0, key="price_sim_change")
            sim_result = _simulate_menu_price_change(menu_sel, price_change, sales_df, menu_df, recipe_df, ingredient_df)
            if sim_result:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("현재 가격", f"{int(sim_result['현재가격']):,}원")
                    st.metric("조정 가격", f"{int(sim_result['조정가격']):,}원")
                with col2:
                    st.metric("예상 판매량", f"{sim_result['예상판매량']:.1f}개")
                    st.metric("예상 매출", f"{int(sim_result['예상매출']):,}원")
                with col3:
                    st.metric("예상 이익", f"{int(sim_result['예상이익']):,}원")
                    st.metric("최적 가격", f"{int(sim_result['최적가격']):,}원")
            else:
                st.info("시뮬레이션 결과를 계산할 수 없습니다.")
        else:
            st.info("메뉴가 없습니다.")


def _render_zone_h_seasonality(seasonality_df):
    """ZONE H: 계절성 분석"""
    render_section_header("🌍 계절성 분석", "🌍")
    
    if seasonality_df.empty:
        st.info("계절성 분석 데이터가 없습니다.")
        return
    
    st.markdown("##### 메뉴별 계절성 지수")
    seasonality_df = seasonality_df.sort_values("계절성지수", ascending=False)
    st.dataframe(seasonality_df, use_container_width=True, hide_index=True, column_config={
        "월별판매량": st.column_config.NumberColumn("월별판매량", format="%,.0f"),
        "계절별판매량": st.column_config.NumberColumn("계절별판매량", format="%,.0f"),
        "계절성지수": st.column_config.NumberColumn("계절성지수", format="%.1f"),
    })
    
    high_season = seasonality_df[seasonality_df["계절성지수"] >= 30]
    if not high_season.empty:
        st.info(f"계절성 메뉴: {', '.join(high_season['메뉴명'].head(5).tolist())} → 계절별 재고 준비 및 프로모션 검토")


def _render_zone_i_actions(monthly_trend_df, summary_df, portfolio_df, lifecycle_df):
    """ZONE I: 메뉴 최적화 액션"""
    render_section_header("💡 메뉴 최적화 액션", "💡")
    
    actions = []
    
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        latest = monthly_trend_df[monthly_trend_df["년월"] == monthly_trend_df["년월"].max()]
        surge = latest[latest["전월대비변화율(%)"] >= 20]
        decline = latest[latest["전월대비변화율(%)"] <= -20]
        if not surge.empty:
            actions.append(f"📈 **판매량 급증** {len(surge)}개: {', '.join(surge['메뉴명'].head(5).tolist())}{' …' if len(surge) > 5 else ''} → 재고 준비량 증가 검토")
        if not decline.empty:
            actions.append(f"📉 **판매량 급감** {len(decline)}개: {', '.join(decline['메뉴명'].head(5).tolist())}{' …' if len(decline) > 5 else ''} → 리뉴얼 또는 삭제 검토")
    
    if summary_df is not None and not summary_df.empty and '이익률' in summary_df.columns:
        low_profit = summary_df[summary_df["이익률"] < 30]
        if not low_profit.empty:
            actions.append(f"💰 **저수익 메뉴** {len(low_profit)}개: {', '.join(low_profit['메뉴명'].head(5).tolist())} → 가격 조정 검토")
    
    if portfolio_df is not None and not portfolio_df.empty:
        role_df = portfolio_df[portfolio_df["구분"] == "역할"]
        if not role_df.empty:
            margin_contrib = role_df[role_df["항목"] == "마진"]["기여도(%)"].iloc[0] if not role_df[role_df["항목"] == "마진"].empty else 0
            if margin_contrib < 20:
                actions.append(f"🎯 **포트폴리오 불균형**: 마진 메뉴 비중이 낮습니다 ({margin_contrib:.1f}%). 마진 메뉴 추가를 검토하세요.")
    
    if lifecycle_df is not None and not lifecycle_df.empty:
        declining = lifecycle_df[lifecycle_df["판매량추세"] == "감소"]
        if not declining.empty:
            actions.append(f"🔄 **판매량 감소 메뉴** {len(declining)}개: {', '.join(declining['메뉴명'].head(5).tolist())} → 리뉴얼 검토")
    
    if not actions:
        st.info("현재 권장 액션이 없습니다.")
        return
    
    for a in actions:
        st.markdown(f"- {a}")


def _render_zone_j_export_actions(sales_df, daily_trend_df, weekday_pattern_df, monthly_trend_df, portfolio_df, correlation_df, store_id):
    """ZONE J: 내보내기 & 액션 (강화)"""
    render_section_header("💾 내보내기 & 액션", "💾")
    
    ts = datetime.now().strftime("%Y%m%d")
    
    def csv_download(df, cols, fname, label, key):
        if df is None or df.empty or not all(c in df.columns for c in cols if c):
            return
        sub = df[[c for c in cols if c in df.columns]]
        csv = sub.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(label=label, data=csv, file_name=fname, mime="text/csv", key=key)
    
    if not sales_df.empty:
        csv_download(sales_df, ["날짜", "메뉴명", "판매수량"], f"일별메뉴판매량_{ts}.csv", "📥 일별 메뉴 판매량 (CSV)", "export_daily_menu")
    
    if monthly_trend_df is not None and not monthly_trend_df.empty:
        csv_download(monthly_trend_df, ["년월", "메뉴명", "판매수량", "전월대비변화율(%)"], f"월별메뉴판매트렌드_{ts}.csv", "📥 월별 메뉴 판매 트렌드 (CSV)", "export_monthly_menu")
    
    if weekday_pattern_df is not None and not weekday_pattern_df.empty:
        csv_download(weekday_pattern_df, ["요일", "메뉴명", "평균판매량", "주말/평일구분"], f"요일별메뉴패턴_{ts}.csv", "📥 요일별 메뉴 패턴 (CSV)", "export_weekday_menu")
    
    if portfolio_df is not None and not portfolio_df.empty:
        csv_download(portfolio_df, ["구분", "항목", "판매량", "매출", "기여도(%)"], f"메뉴포트폴리오_{ts}.csv", "📥 메뉴 포트폴리오 분석 (CSV)", "export_portfolio")
    
    if correlation_df is not None and not correlation_df.empty:
        csv_download(correlation_df, ["메뉴A", "메뉴B", "상관계수", "상관유형"], f"메뉴상관관계_{ts}.csv", "📥 메뉴 상관관계 (CSV)", "export_correlation")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 판매 입력으로 이동", key="go_to_sales", use_container_width=True):
            st.session_state["current_page"] = "판매 입력"
            st.rerun()
    with col2:
        if st.button("📝 메뉴 입력으로 이동", key="go_to_menu", use_container_width=True):
            st.session_state["current_page"] = "판매 메뉴 입력"
            st.rerun()


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_analysis()
