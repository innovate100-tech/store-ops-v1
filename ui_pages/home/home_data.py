"""
홈 전용 경량 데이터 로더
- load_home_kpis: 홈 최초 진입 시 KPI만 로드
- get_monthly_close_stats: 마감률/스트릭
- get_menu_count, get_close_count, check_actual_settlement_exists
- detect_data_level, detect_owner_day_level
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple

from src.auth import get_supabase_client
from src.storage_supabase import load_monthly_sales_total, load_monthly_settlement_snapshot


def get_monthly_close_stats(store_id: str, year: int, month: int) -> Tuple[int, int, float, int]:
    """
    이번 달 마감률과 연속 마감(스트릭) 계산
    Returns: (closed_days, total_days, close_rate, streak_days)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return (0, 0, 0.0, 0)
        start_date = date(year, month, 1)
        end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        total_days = (end_date - start_date).days
        result = supabase.table("daily_close").select("date").eq("store_id", store_id).gte(
            "date", start_date.isoformat()
        ).lt("date", end_date.isoformat()).order("date", desc=True).execute()
        if not result.data:
            return (0, total_days, 0.0, 0)
        closed_days = len(result.data)
        close_rate = closed_days / total_days if total_days > 0 else 0.0
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        closed_dates = {r["date"] for r in result.data if r.get("date")}
        streak_days = 0
        check = today
        while start_date <= check < end_date:
            if check.isoformat() in closed_dates:
                streak_days += 1
                check -= timedelta(days=1)
            else:
                break
        return (closed_days, total_days, close_rate, streak_days)
    except Exception:
        return (0, 0, 0.0, 0)


@st.cache_data(ttl=300)
def load_home_kpis(store_id: str, year: int, month: int) -> dict:
    """
    홈 최초 진입 시 필요한 핵심 KPI만 로드.
    Returns: monthly_sales, yesterday_sales, close_stats, revenue_per_visit, monthly_profit, target_sales, target_ratio
    """
    out = {
        "monthly_sales": 0,
        "yesterday_sales": 0,
        "close_stats": (0, 0, 0.0, 0),
        "revenue_per_visit": None,
        "monthly_profit": None,
        "target_sales": 0,
        "target_ratio": None,
    }
    if not store_id:
        return out
    try:
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        today = now.date()
        yesterday = today - timedelta(days=1)
        start = f"{year}-{month:02d}-01"
        end = f"{year + 1}-01-01" if month == 12 else f"{year}-{month + 1:02d}-01"

        monthly_sales = load_monthly_sales_total(store_id, year, month)
        out["monthly_sales"] = monthly_sales or 0
        out["close_stats"] = get_monthly_close_stats(store_id, year, month)

        supabase = get_supabase_client()
        if supabase:
            # 어제 매출 또는 마지막 마감 매출 조회
            yesterday_close = supabase.table("daily_close").select("total_sales, date").eq(
                "store_id", store_id
            ).eq("date", yesterday.isoformat()).limit(1).execute()
            if yesterday_close.data and len(yesterday_close.data) > 0:
                v = yesterday_close.data[0].get("total_sales")
                if v is not None:
                    out["yesterday_sales"] = int(float(v or 0))
            else:
                # 어제 마감이 없으면 최근 마감 매출 조회
                last_close = supabase.table("daily_close").select("total_sales, date").eq(
                    "store_id", store_id
                ).lt("date", today.isoformat()).order("date", desc=True).limit(1).execute()
                if last_close.data and len(last_close.data) > 0:
                    v = last_close.data[0].get("total_sales")
                    if v is not None:
                        out["yesterday_sales"] = int(float(v or 0))

            # 유입당 매출 계산 (네이버 유입 기준)
            if monthly_sales and monthly_sales > 0:
                naver_visits = supabase.table("naver_visitors").select("visitors").eq(
                    "store_id", store_id
                ).gte("date", start).lt("date", end).execute()
                if naver_visits.data:
                    tot_visits = sum(int(r.get("visitors", 0) or 0) for r in naver_visits.data)
                    if tot_visits > 0:
                        out["revenue_per_visit"] = int(monthly_sales / tot_visits)

            # 목표 매출 조회
            target_result = supabase.table("targets").select("target_sales").eq(
                "store_id", store_id
            ).eq("year", year).eq("month", month).limit(1).execute()
            if target_result.data and len(target_result.data) > 0:
                target_sales = target_result.data[0].get("target_sales")
                if target_sales is not None:
                    out["target_sales"] = int(float(target_sales or 0))
                    if out["target_sales"] > 0 and monthly_sales > 0:
                        out["target_ratio"] = round((monthly_sales / out["target_sales"]) * 100, 1)

        snap = load_monthly_settlement_snapshot(store_id, year, month)
        if snap and snap.get("operating_profit") is not None:
            out["monthly_profit"] = int(snap.get("operating_profit", 0))
    except Exception:
        pass
    return out


def get_menu_count(store_id: str) -> int:
    """메뉴 개수 (온보딩 미션용)."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        r = supabase.table("menu_master").select("id", count="exact").eq("store_id", store_id).execute()
        c = r.count if hasattr(r, "count") and r.count is not None else (len(r.data) if r.data else 0)
        return c
    except Exception:
        return 0


def get_close_count(store_id: str) -> int:
    """점장마감 개수 (온보딩 미션용)."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        r = supabase.table("daily_close").select("id", count="exact").eq("store_id", store_id).execute()
        c = r.count if hasattr(r, "count") and r.count is not None else (len(r.data) if r.data else 0)
        return c
    except Exception:
        return 0


def check_actual_settlement_exists(store_id: str, year: int, month: int) -> bool:
    """이번 달 actual_settlement 존재 여부."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        r = supabase.table("actual_settlement").select("id", count="exact").eq(
            "store_id", store_id
        ).eq("year", year).eq("month", month).limit(1).execute()
        c = r.count if hasattr(r, "count") and r.count is not None else (len(r.data) if r.data else 0)
        return c > 0
    except Exception:
        return False


def detect_data_level(store_id: str) -> int:
    """
    데이터 성숙도 (0–3). UI 노출 금지, 내부 gating용.
    LEVEL 0: sales 0건 / LEVEL 1: sales 있음, daily_close 3건 이하
    LEVEL 2: daily_close 4건+ 또는 daily_sales_items / LEVEL 3: expense_structure 또는 actual_settlement
    """
    if not store_id:
        return 0
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        sc = supabase.table("sales").select("id", count="exact").eq("store_id", store_id).limit(1).execute()
        sales_count = sc.count if hasattr(sc, "count") and sc.count is not None else (len(sc.data) if sc.data else 0)
        if sales_count == 0:
            return 0
        dc = supabase.table("daily_close").select("id", count="exact").eq("store_id", store_id).limit(1).execute()
        daily_close_count = dc.count if hasattr(dc, "count") and dc.count is not None else (len(dc.data) if dc.data else 0)
        if daily_close_count <= 3:
            return 1
        dsi = supabase.table("v_daily_sales_items_effective").select("menu_id", count="exact").eq("store_id", store_id).limit(1).execute()
        daily_sales_count = dsi.count if hasattr(dsi, "count") and dsi.count is not None else (len(dsi.data) if dsi.data else 0)
        if daily_close_count > 3 or daily_sales_count > 0:
            try:
                ec = supabase.table("expense_structure").select("id", count="exact").eq("store_id", store_id).limit(1).execute()
                ecn = ec.count if hasattr(ec, "count") and ec.count is not None else (len(ec.data) if ec.data else 0)
                if ecn > 0:
                    return 3
            except Exception:
                pass
            try:
                ac = supabase.table("actual_settlement").select("id", count="exact").eq("store_id", store_id).limit(1).execute()
                acn = ac.count if hasattr(ac, "count") and ac.count is not None else (len(ac.data) if ac.data else 0)
                if acn > 0:
                    return 3
            except Exception:
                pass
            return 2
        return 1
    except Exception:
        return 0


def detect_owner_day_level(store_id: str) -> str | None:
    """DAY1/DAY3/DAY7 판별. 연출용만, UI 노출 금지."""
    try:
        n = get_close_count(store_id)
        if n > 0 and n < 3:
            return "DAY1"
        if n >= 3:
            kst = ZoneInfo("Asia/Seoul")
            now = datetime.now(kst)
            if check_actual_settlement_exists(store_id, now.year, now.month):
                return "DAY7"
            return "DAY3"
        return None
    except Exception:
        return None
