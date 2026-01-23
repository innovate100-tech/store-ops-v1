"""
홈 문제/잘한 점 룰 (룰 기반)
- get_problems_top3, get_good_points_top3
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from src.auth import get_supabase_client
from ui_pages.home.home_data import get_monthly_close_stats


def get_problems_top3(store_id: str) -> list:
    """
    문제 TOP3 추출 (룰 기반)
    Returns: [{"text": str, "target_page": str}, ...] 최대 3개
    """
    problems = []
    try:
        supabase = get_supabase_client()
        if not supabase:
            return [{"text": "데이터를 불러올 수 없습니다.", "target_page": "점장 마감"}]
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        six_days_ago = today - timedelta(days=6)
        sales_recent = supabase.table("sales").select("date, total_sales").eq("store_id", store_id).gte(
            "date", six_days_ago.isoformat()
        ).lte("date", today.isoformat()).order("date", desc=False).execute()
        sales_data = {}
        if sales_recent.data:
            for row in sales_recent.data:
                d = row.get("date")
                t = float(row.get("total_sales", 0) or 0)
                if d:
                    sales_data[d] = t
        if len(sales_data) >= 6:
            r3 = list(sales_data.values())[-3:]
            p3 = list(sales_data.values())[-6:-3]
            if r3 and p3:
                ra = sum(r3) / len(r3)
                pa = sum(p3) / len(p3)
                if ra < pa and pa > 0:
                    problems.append({"text": "최근 3일 평균 매출이 직전 기간보다 감소했습니다.", "target_page": "매출 관리"})
        cy, cm = today.year, today.month
        start_m = date(cy, cm, 1)
        end_m = date(cy + 1, 1, 1) if cm == 12 else date(cy, cm + 1, 1)
        sales_month = supabase.table("sales").select("date, total_sales").eq("store_id", store_id).gte(
            "date", start_m.isoformat()
        ).lt("date", end_m.isoformat()).execute()
        month_sales = {}
        if sales_month.data:
            for row in sales_month.data:
                d = row.get("date")
                t = float(row.get("total_sales", 0) or 0)
                if d and t > 0:
                    month_sales[d] = t
        if month_sales:
            mn = min(month_sales.values())
            md = min((d for d, s in month_sales.items() if s == mn))
            md = datetime.strptime(md, "%Y-%m-%d").date() if isinstance(md, str) else md
            if 0 <= (today - md).days <= 3:
                problems.append({"text": "이번 달 최저 매출일이 최근에 발생했습니다.", "target_page": "매출 관리"})
        dc_month = supabase.table("daily_close").select("date").eq("store_id", store_id).gte(
            "date", start_m.isoformat()
        ).lt("date", end_m.isoformat()).execute()
        closed = {r["date"] for r in (dc_month.data or []) if r.get("date")}
        d = start_m
        gap = False
        while d < today and d < end_m:
            if d.isoformat() not in closed:
                gap = True
                break
            d += timedelta(days=1)
        if gap:
            problems.append({"text": "이번 달 마감하지 않은 날이 있습니다.", "target_page": "점장 마감"})
        seven_ago = today - timedelta(days=7)
        si = supabase.table("v_daily_sales_items_effective").select("menu_id, qty, date").eq(
            "store_id", store_id
        ).gte("date", seven_ago.isoformat()).lte("date", today.isoformat()).execute()
        if si.data:
            mt, tq = {}, 0
            for r in si.data:
                mid = r.get("menu_id")
                q = int(r.get("qty", 0) or 0)
                if mid and q > 0:
                    mt[mid] = mt.get(mid, 0) + q
                    tq += q
            if mt and tq > 0 and max(mt.values()) / tq >= 0.5:
                problems.append({"text": "상위 1개 메뉴가 전체 판매의 50% 이상을 차지합니다.", "target_page": "판매 관리"})
            ud = {r.get("date") for r in si.data if r.get("date")}
            if len(ud) <= 2:
                problems.append({"text": "최근 일주일 판매 데이터가 거의 없습니다.", "target_page": "점장 마감"})
        return problems[:3] if problems else [{"text": "아직 분석할 데이터가 충분하지 않습니다.", "target_page": "점장 마감"}]
    except Exception:
        return [{"text": "문제 분석 중 오류가 발생했습니다.", "target_page": "점장 마감"}]


def get_good_points_top3(store_id: str) -> list:
    """
    잘한 점 TOP3 추출 (룰 기반)
    Returns: [{"text": str, "target_page": str}, ...] 최대 3개
    """
    good_points = []
    try:
        supabase = get_supabase_client()
        if not supabase:
            return [{"text": "데이터를 불러올 수 없습니다.", "target_page": "점장 마감"}]
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        six_days_ago = today - timedelta(days=6)
        sales_recent = supabase.table("sales").select("date, total_sales").eq("store_id", store_id).gte(
            "date", six_days_ago.isoformat()
        ).lte("date", today.isoformat()).order("date", desc=False).execute()
        sales_data = {}
        if sales_recent.data:
            for row in sales_recent.data:
                d = row.get("date")
                t = float(row.get("total_sales", 0) or 0)
                if d:
                    sales_data[d] = t
        if len(sales_data) >= 6:
            r3 = list(sales_data.values())[-3:]
            p3 = list(sales_data.values())[-6:-3]
            if r3 and p3 and sum(p3) / len(p3) > 0 and sum(r3) / len(r3) > sum(p3) / len(p3):
                good_points.append({"text": "최근 3일 평균 매출이 이전 기간보다 증가했습니다.", "target_page": "매출 관리"})
        cy, cm = today.year, today.month
        start_m = date(cy, cm, 1)
        end_m = date(cy + 1, 1, 1) if cm == 12 else date(cy, cm + 1, 1)
        sales_month = supabase.table("sales").select("date, total_sales").eq("store_id", store_id).gte(
            "date", start_m.isoformat()
        ).lt("date", end_m.isoformat()).execute()
        month_sales = {}
        if sales_month.data:
            for row in sales_month.data:
                d = row.get("date")
                t = float(row.get("total_sales", 0) or 0)
                if d and t > 0:
                    month_sales[d] = t
        if month_sales:
            mx = max(month_sales.values())
            md = max((d for d, s in month_sales.items() if s == mx))
            md = datetime.strptime(md, "%Y-%m-%d").date() if isinstance(md, str) else md
            if 0 <= (today - md).days <= 3:
                good_points.append({"text": "이번 달 최고 매출일이 최근에 발생했습니다.", "target_page": "매출 관리"})
        close_stats = get_monthly_close_stats(store_id, cy, cm)
        if close_stats[3] >= 3:
            good_points.append({"text": "연속 마감 기록이 유지되고 있습니다.", "target_page": "점장 마감"})
        seven_ago = today - timedelta(days=7)
        si = supabase.table("v_daily_sales_items_effective").select("menu_id, qty, date").eq(
            "store_id", store_id
        ).gte("date", seven_ago.isoformat()).lte("date", today.isoformat()).execute()
        if si.data:
            mt, tq = {}, 0
            for r in si.data:
                mid = r.get("menu_id")
                q = int(r.get("qty", 0) or 0)
                if mid and q > 0:
                    mt[mid] = mt.get(mid, 0) + q
                    tq += q
            if mt and tq > 0 and max(mt.values()) / tq < 0.5 and len(mt) >= 3:
                good_points.append({"text": "최근 판매가 여러 메뉴로 분산되고 있습니다.", "target_page": "판매 관리"})
            ud = {r.get("date") for r in si.data if r.get("date")}
            if len(ud) >= 5:
                good_points.append({"text": "최근 일주일 판매 입력이 꾸준히 이루어지고 있습니다.", "target_page": "판매 관리"})
        return good_points[:3] if good_points else [{"text": "데이터가 쌓이면 자동 분석됩니다.", "target_page": "점장 마감"}]
    except Exception:
        return [{"text": "잘한 점 분석 중 오류가 발생했습니다.", "target_page": "점장 마감"}]
