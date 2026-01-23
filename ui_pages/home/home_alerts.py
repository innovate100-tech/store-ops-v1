"""
홈 이상 징후 (룰 기반)
- get_anomaly_signals
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from src.auth import get_supabase_client


def get_anomaly_signals(store_id: str) -> list:
    """
    이상 징후 감지 (조기경보, 룰 기반)
    Returns: [{"icon": str, "text": str, "target_page": str}, ...] 최대 3개
    """
    signals = []
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        seven_ago = today - timedelta(days=7)
        sales_recent = supabase.table("sales").select("date, total_sales").eq("store_id", store_id).gte(
            "date", seven_ago.isoformat()
        ).lte("date", today.isoformat()).order("date", desc=False).execute()
        sales_data = {}
        if sales_recent.data:
            for row in sales_recent.data:
                d = row.get("date")
                t = float(row.get("total_sales", 0) or 0)
                if d and t > 0:
                    sales_data[d] = t
        if len(sales_data) >= 3:
            recent_dates = sorted(sales_data.keys())[-3:]
            recent_values = [sales_data[d] for d in recent_dates]
            if len(recent_values) == 3 and recent_values[0] > recent_values[1] > recent_values[2]:
                signals.append({"icon": "📉", "text": "최근 3일 연속 매출이 감소하고 있습니다.", "target_page": "매출 관리"})
                if len(signals) >= 3:
                    return signals[:3]
        expected = set()
        d = seven_ago
        while d <= today:
            expected.add(d.isoformat())
            d += timedelta(days=1)
        missing = expected - set(sales_data.keys())
        if len(missing) >= 2:
            signals.append({"icon": "⚠️", "text": "최근 7일 중 매출이 입력되지 않은 날이 2일 이상 있습니다.", "target_page": "매출 관리"})
            if len(signals) >= 3:
                return signals[:3]
        cy, cm = today.year, today.month
        start_m = date(cy, cm, 1)
        end_m = date(cy + 1, 1, 1) if cm == 12 else date(cy, cm + 1, 1)
        sales_month = supabase.table("sales").select("date, total_sales").eq("store_id", store_id).gte(
            "date", start_m.isoformat()
        ).lt("date", end_m.isoformat()).execute()
        month_sales_list = []
        if sales_month.data:
            for row in sales_month.data:
                t = float(row.get("total_sales", 0) or 0)
                if t > 0:
                    month_sales_list.append(t)
        if len(sales_data) >= 3 and len(month_sales_list) >= 3:
            r3 = list(sales_data.values())[-3:]
            recent_avg = sum(r3) / len(r3)
            month_avg = sum(month_sales_list) / len(month_sales_list)
            if month_avg > 0:
                ratio = recent_avg / month_avg
                if ratio <= 0.7 or ratio >= 1.3:
                    signals.append({"icon": "📊", "text": "최근 매출 흐름이 이번 달 평균 대비 크게 변했습니다.", "target_page": "매출 관리"})
                    if len(signals) >= 3:
                        return signals[:3]
        recent_3_start = today - timedelta(days=3)
        prev_3_start = today - timedelta(days=6)
        s3 = supabase.table("v_daily_sales_items_effective").select("menu_id, qty").eq(
            "store_id", store_id
        ).gte("date", recent_3_start.isoformat()).lte("date", today.isoformat()).execute()
        p3 = supabase.table("v_daily_sales_items_effective").select("menu_id, qty").eq(
            "store_id", store_id
        ).gte("date", prev_3_start.isoformat()).lt("date", recent_3_start.isoformat()).execute()
        if s3.data and p3.data:
            rmt, rtot = {}, 0
            for r in s3.data:
                mid = r.get("menu_id")
                q = int(r.get("qty", 0) or 0)
                if mid and q > 0:
                    rmt[mid] = rmt.get(mid, 0) + q
                    rtot += q
            pmt, ptot = {}, 0
            for r in p3.data:
                mid = r.get("menu_id")
                q = int(r.get("qty", 0) or 0)
                if mid and q > 0:
                    pmt[mid] = pmt.get(mid, 0) + q
                    ptot += q
            if rtot > 0 and ptot > 0:
                for mid in rmt:
                    rr = rmt[mid] / rtot
                    pr = pmt.get(mid, 0) / ptot
                    if pr > 0 and rr >= pr * 1.5:
                        signals.append({"icon": "🍽️", "text": "최근 판매에서 특정 메뉴 비중이 급격히 증가했습니다.", "target_page": "판매 관리"})
                        if len(signals) >= 3:
                            return signals[:3]
                        break
        five_ago = today - timedelta(days=5)
        s5 = supabase.table("v_daily_sales_items_effective").select("qty").eq("store_id", store_id).gte(
            "date", five_ago.isoformat()
        ).lte("date", today.isoformat()).execute()
        p5 = supabase.table("v_daily_sales_items_effective").select("qty").eq("store_id", store_id).gte(
            "date", (five_ago - timedelta(days=5)).isoformat()
        ).lt("date", five_ago.isoformat()).execute()
        if s5.data and p5.data:
            rq = sum(int(r.get("qty", 0) or 0) for r in s5.data)
            pq = sum(int(r.get("qty", 0) or 0) for r in p5.data)
            if pq > 0 and rq / pq <= 0.7:
                signals.append({"icon": "📉", "text": "최근 판매량이 눈에 띄게 줄었습니다.", "target_page": "판매 관리"})
                if len(signals) >= 3:
                    return signals[:3]
        dc = supabase.table("daily_close").select("date").eq("store_id", store_id).gte(
            "date", (today - timedelta(days=3)).isoformat()
        ).lte("date", today.isoformat()).execute()
        closed = {r["date"] for r in (dc.data or []) if r.get("date")}
        missing_close = 0
        d = today - timedelta(days=2)
        while d <= today:
            if d.isoformat() not in closed:
                missing_close += 1
            d += timedelta(days=1)
        if missing_close >= 3:
            signals.append({"icon": "⏰", "text": "최근 3일 연속 마감이 없습니다.", "target_page": "점장 마감"})
        return signals[:3]
    except Exception:
        return []
