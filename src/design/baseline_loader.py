"""
기준 구조(Baseline) 로더
분석 데이터(매출·비용·원가)에서 현재 월 손익 구조를 수집해 설계 기준안으로 변환
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from calendar import monthrange
from typing import Any

import pandas as pd
import streamlit as st

from src.storage_supabase import (
    load_csv,
    load_monthly_sales_total,
    load_best_available_daily_sales,
    get_fixed_costs,
    get_variable_cost_ratio,
    load_expense_structure,
)
from src.analytics import calculate_menu_cost


def _forecast_monthly_sales(store_id: str, year: int, month: int) -> float:
    """이번 달 예상 매출 (경과일 기준 추정)"""
    try:
        monthly = load_monthly_sales_total(store_id, year, month) or 0
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        first = datetime(year, month, 1).date()
        if today.year == year and today.month == month:
            days_passed = (today - first).days + 1
            total_days = monthrange(year, month)[1]
            if days_passed > 0 and total_days > 0:
                return (monthly / days_passed) * total_days
        return float(monthly)
    except Exception:
        return 0.0


def load_baseline_structure(store_id: str, year: int, month: int) -> dict[str, Any]:
    """
    분석 데이터에서 기준 구조 자동 수집.
    설계 전용 세션 키에 저장한 뒤 반환.
    """
    # 월 구간
    kst = ZoneInfo("Asia/Seoul")
    first = datetime(year, month, 1, tzinfo=kst).date()
    last_day = monthrange(year, month)[1]
    last = datetime(year, month, last_day, tzinfo=kst).date()
    start_str = first.isoformat()
    end_str = last.isoformat()

    # 일별 매출·방문자
    daily_df = load_best_available_daily_sales(store_id=store_id, start_date=start_str, end_date=end_str)
    daily_visitors = 0.0
    daily_sales_avg = 0.0
    operating_days = 30
    if not daily_df.empty and "date" in daily_df.columns:
        valid = daily_df.dropna(subset=["total_sales"])
        if not valid.empty:
            daily_sales_avg = float(valid["total_sales"].mean())
        if "visitors" in daily_df.columns:
            v = daily_df["visitors"].dropna()
            if not v.empty:
                daily_visitors = float(v.mean())
        operating_days = max(1, len(daily_df))

    # 객단가: 일매출/일방문객 (방문자 없으면 0)
    avg_price_per_customer = 0.0
    if daily_visitors > 0 and daily_sales_avg > 0:
        avg_price_per_customer = daily_sales_avg / daily_visitors

    # 회전율: 별도 좌석 수 없으면 일방문객으로 대체 (1인당 1회전 가정)
    turnover_rate = daily_visitors if daily_visitors > 0 else 1.0

    # 월매출·예상매출
    monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
    forecast_sales = _forecast_monthly_sales(store_id, year, month)

    # 비용
    fixed_costs = get_fixed_costs(store_id, year, month) or 0.0
    variable_ratio = get_variable_cost_ratio(store_id, year, month) or 0.0
    break_even = 0.0
    if variable_ratio is not None and variable_ratio < 1.0 and fixed_costs > 0:
        break_even = fixed_costs / (1.0 - variable_ratio)

    # 인건비율·원가율 (expense / 원가 분석)
    labor_cost_ratio = None
    try:
        exp_df = load_expense_structure(year, month, store_id=store_id)
        if isinstance(exp_df, pd.DataFrame) and not exp_df.empty:
            labor_row = exp_df[exp_df["category"] == "인건비"]
            labor_total = float(labor_row["amount"].sum()) if not labor_row.empty else 0
            total_sales = monthly_sales or forecast_sales or 1
            if total_sales > 0:
                labor_cost_ratio = labor_total / total_sales
    except Exception:
        pass

    avg_cost_rate = None
    try:
        menu_df = load_csv("menu_master.csv", store_id=store_id, default_columns=["메뉴명", "판매가"])
        recipe_df = load_csv("recipes.csv", store_id=store_id, default_columns=["메뉴명", "재료명", "사용량"])
        ing_df = load_csv("ingredient_master.csv", store_id=store_id, default_columns=["재료명", "단위", "단가"])
        if not menu_df.empty and not recipe_df.empty and not ing_df.empty:
            cost_df = calculate_menu_cost(menu_df, recipe_df, ing_df)
            if not cost_df.empty and "원가" in cost_df.columns and "판매가" in cost_df.columns:
                cost_df = cost_df.copy()
                cost_df["원가율"] = cost_df["원가"] / cost_df["판매가"].replace(0, 1)
                avg_cost_rate = float(cost_df["원가율"].mean())
    except Exception:
        pass

    baseline = {
        "sales": {
            "daily_visitors": daily_visitors,
            "avg_price_per_customer": avg_price_per_customer,
            "turnover_rate": turnover_rate,
            "operating_days": operating_days,
            "monthly_sales": float(monthly_sales),
            "forecast_sales": forecast_sales,
        },
        "cost": {
            "fixed_costs": float(fixed_costs),
            "variable_cost_ratio": float(variable_ratio) if variable_ratio is not None else 0.0,
            "labor_cost_ratio": labor_cost_ratio,
        },
        "profit": {
            "break_even_sales": break_even,
            "expected_profit": forecast_sales - (fixed_costs + forecast_sales * (variable_ratio or 0)) if forecast_sales else 0,
        },
        "menu": {
            "avg_cost_rate": avg_cost_rate,
        },
        "loaded_at": datetime.now(kst).isoformat(),
        "year": year,
        "month": month,
        "store_id": store_id,
    }

    key = f"_baseline_structure_{store_id}_{year}_{month}"
    st.session_state[key] = baseline
    return baseline


def get_baseline_structure(store_id: str, year: int, month: int) -> dict[str, Any] | None:
    """세션에 저장된 기준 구조 반환. 없으면 None."""
    key = f"_baseline_structure_{store_id}_{year}_{month}"
    return st.session_state.get(key)
