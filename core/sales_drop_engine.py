"""
매출 하락 원인 분석 엔진
- 언제부터 떨어졌나?
- 무엇이 떨어졌나?
- 어디를 고치나?
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Tuple

from src.storage_supabase import (
    load_best_available_daily_sales,
    load_csv,
)


@st.cache_data(ttl=300)
def analyze_sales_drop(
    period_days: int,
    compare_type: str,  # "week" | "month"
    store_id: str,
    base_date: Optional[date] = None
) -> Dict:
    """
    매출 하락 원인 분석
    
    Args:
        period_days: 분석 기간 (7/14/30)
        compare_type: 비교 방식 ("week" | "month")
        store_id: 매장 ID
        base_date: 기준 날짜 (없으면 오늘)
    
    Returns:
        {
            "summary": {
                "sales_delta_pct": float,
                "visitors_delta_pct": float,
                "avgp_delta_pct": float,
                "quantity_delta_pct": float,
                "drop_start_date": date,
                "recent_trend": str,
            },
            "metrics": {
                "recent": {...},
                "baseline": {...},
                "delta": {...},
            },
            "menu_changes": [
                {
                    "menu_name": str,
                    "qty_delta_pct": float,
                    "sales_delta_pct": float,
                    "rank_change": int,
                }
            ],
            "primary_cause": "traffic" | "menu" | "price" | "cost" | "structure",
            "confidence": int,  # 0-100
            "evidence": List[str],
        }
    """
    if not store_id:
        return _get_empty_result()
    
    try:
        kst = ZoneInfo("Asia/Seoul")
        if base_date is None:
            base_date = datetime.now(kst).date()
        
        # 기간 계산
        recent_end = base_date
        recent_start = base_date - timedelta(days=period_days - 1)
        
        if compare_type == "week":
            # 전주 대비: 7일 shift
            baseline_end = recent_start - timedelta(days=1)
            baseline_start = baseline_end - timedelta(days=period_days - 1)
        else:  # month
            # 전월 대비: 28일 shift (간단화)
            baseline_end = recent_start - timedelta(days=1)
            baseline_start = baseline_end - timedelta(days=period_days - 1)
        
        # 데이터 로드
        start_date = (baseline_start - timedelta(days=2)).isoformat()
        end_date = recent_end.isoformat()
        
        sales_df = load_best_available_daily_sales(
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if sales_df.empty:
            return _get_empty_result()
        
        # 날짜 변환
        sales_df['date'] = sales_df['date'].apply(
            lambda x: x.date() if isinstance(x, datetime) else x
        )
        
        # Baseline 계산
        baseline_df = sales_df[
            (sales_df['date'] >= baseline_start) &
            (sales_df['date'] <= baseline_end)
        ]
        
        # Recent 계산
        recent_df = sales_df[
            (sales_df['date'] >= recent_start) &
            (sales_df['date'] <= recent_end)
        ]
        
        if baseline_df.empty or recent_df.empty:
            return _get_empty_result()
        
        # 지표 계산
        baseline_sales = baseline_df['total_sales'].mean() if 'total_sales' in baseline_df.columns else 0
        recent_sales = recent_df['total_sales'].mean() if 'total_sales' in recent_df.columns else 0
        
        baseline_visitors = baseline_df['visitors'].mean() if 'visitors' in baseline_df.columns else 0
        recent_visitors = recent_df['visitors'].mean() if 'visitors' in recent_df.columns else 0
        
        baseline_avgp = (baseline_sales / baseline_visitors) if baseline_visitors > 0 else 0
        recent_avgp = (recent_sales / recent_visitors) if recent_visitors > 0 else 0
        
        # 판매량 계산 (daily_sales_items 기반)
        quantity_delta_pct = _calculate_quantity_delta(
            store_id, baseline_start, baseline_end, recent_start, recent_end
        )
        
        # 변화율 계산
        sales_delta_pct = ((recent_sales - baseline_sales) / baseline_sales * 100) if baseline_sales > 0 else 0
        visitors_delta_pct = ((recent_visitors - baseline_visitors) / baseline_visitors * 100) if baseline_visitors > 0 else 0
        avgp_delta_pct = ((recent_avgp - baseline_avgp) / baseline_avgp * 100) if baseline_avgp > 0 else 0
        
        # 하락 시작일 추정
        drop_start_date = _estimate_drop_start_date(sales_df, baseline_sales, recent_start)
        
        # 최근 추세
        recent_trend = _calculate_recent_trend(recent_df)
        
        # 메뉴 변화 분석
        menu_changes = _analyze_menu_changes(
            store_id, baseline_start, baseline_end, recent_start, recent_end
        )
        
        # 원인 분류
        primary_cause, confidence, evidence = _classify_primary_cause(
            sales_delta_pct,
            visitors_delta_pct,
            avgp_delta_pct,
            quantity_delta_pct,
            menu_changes
        )
        
        return {
            "summary": {
                "sales_delta_pct": sales_delta_pct,
                "visitors_delta_pct": visitors_delta_pct,
                "avgp_delta_pct": avgp_delta_pct,
                "quantity_delta_pct": quantity_delta_pct,
                "drop_start_date": drop_start_date,
                "recent_trend": recent_trend,
            },
            "metrics": {
                "recent": {
                    "sales_avg": recent_sales,
                    "visitors_avg": recent_visitors,
                    "avgp": recent_avgp,
                },
                "baseline": {
                    "sales_avg": baseline_sales,
                    "visitors_avg": baseline_visitors,
                    "avgp": baseline_avgp,
                },
                "delta": {
                    "sales_delta_pct": sales_delta_pct,
                    "visitors_delta_pct": visitors_delta_pct,
                    "avgp_delta_pct": avgp_delta_pct,
                    "quantity_delta_pct": quantity_delta_pct,
                },
            },
            "menu_changes": menu_changes,
            "primary_cause": primary_cause,
            "confidence": confidence,
            "evidence": evidence,
        }
    except Exception as e:
        return _get_empty_result()


def _get_empty_result() -> Dict:
    """빈 결과 반환"""
    return {
        "summary": {
            "sales_delta_pct": 0.0,
            "visitors_delta_pct": 0.0,
            "avgp_delta_pct": 0.0,
            "quantity_delta_pct": 0.0,
            "drop_start_date": None,
            "recent_trend": "데이터 부족",
        },
        "metrics": {
            "recent": {},
            "baseline": {},
            "delta": {},
        },
        "menu_changes": [],
        "primary_cause": None,
        "confidence": 0,
        "evidence": [],
    }


def _calculate_quantity_delta(
    store_id: str,
    baseline_start: date,
    baseline_end: date,
    recent_start: date,
    recent_end: date
) -> float:
    """판매량 변화율 계산"""
    try:
        # daily_sales_items 기반 집계
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            return 0.0
        
        # Baseline 판매량
        baseline_result = supabase.table("v_daily_sales_items_effective")\
            .select("qty")\
            .eq("store_id", store_id)\
            .gte("date", baseline_start.isoformat())\
            .lte("date", baseline_end.isoformat())\
            .execute()
        
        baseline_qty = sum(row.get("qty", 0) for row in baseline_result.data) if baseline_result.data else 0
        baseline_days = (baseline_end - baseline_start).days + 1
        baseline_avg = baseline_qty / baseline_days if baseline_days > 0 else 0
        
        # Recent 판매량
        recent_result = supabase.table("v_daily_sales_items_effective")\
            .select("qty")\
            .eq("store_id", store_id)\
            .gte("date", recent_start.isoformat())\
            .lte("date", recent_end.isoformat())\
            .execute()
        
        recent_qty = sum(row.get("qty", 0) for row in recent_result.data) if recent_result.data else 0
        recent_days = (recent_end - recent_start).days + 1
        recent_avg = recent_qty / recent_days if recent_days > 0 else 0
        
        # 변화율
        if baseline_avg > 0:
            return ((recent_avg - baseline_avg) / baseline_avg * 100)
        return 0.0
    except Exception:
        return 0.0


def _estimate_drop_start_date(sales_df, baseline_avg: float, recent_start: date) -> Optional[date]:
    """하락 시작일 추정"""
    try:
        # rolling average가 baseline 아래로 지속되는 최초일
        threshold = baseline_avg * 0.95  # 5% 하락 기준
        
        for check_date in sorted(sales_df['date'].unique(), reverse=True):
            if check_date < recent_start:
                continue
            
            window_df = sales_df[
                (sales_df['date'] >= check_date - timedelta(days=2)) &
                (sales_df['date'] <= check_date)
            ]
            
            if not window_df.empty:
                window_avg = window_df['total_sales'].mean() if 'total_sales' in window_df.columns else 0
                if window_avg < threshold:
                    return check_date
        
        return recent_start
    except Exception:
        return None


def _calculate_recent_trend(recent_df) -> str:
    """최근 추세 계산"""
    try:
        if len(recent_df) < 3:
            return "데이터 부족"
        
        # 최근 3일 vs 이전 3일
        sorted_df = recent_df.sort_values('date')
        first_half = sorted_df.head(3)
        second_half = sorted_df.tail(3)
        
        first_avg = first_half['total_sales'].mean() if 'total_sales' in first_half.columns else 0
        second_avg = second_half['total_sales'].mean() if 'total_sales' in second_half.columns else 0
        
        if second_avg > first_avg * 1.05:
            return "회복 중"
        elif second_avg < first_avg * 0.95:
            return "추가 하락"
        else:
            return "정체"
    except Exception:
        return "데이터 부족"


def _analyze_menu_changes(
    store_id: str,
    baseline_start: date,
    baseline_end: date,
    recent_start: date,
    recent_end: date
) -> List[Dict]:
    """상위 메뉴 변화 분석"""
    try:
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # Baseline Top5
        baseline_result = supabase.table("v_daily_sales_items_effective")\
            .select("menu_name, qty, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", baseline_start.isoformat())\
            .lte("date", baseline_end.isoformat())\
            .execute()
        
        baseline_menus = {}
        for row in baseline_result.data:
            menu_name = row.get("menu_name", "")
            if menu_name:
                baseline_menus[menu_name] = baseline_menus.get(menu_name, 0) + row.get("qty", 0)
        
        baseline_top5 = sorted(baseline_menus.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Recent Top5
        recent_result = supabase.table("v_daily_sales_items_effective")\
            .select("menu_name, qty, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", recent_start.isoformat())\
            .lte("date", recent_end.isoformat())\
            .execute()
        
        recent_menus = {}
        for row in recent_result.data:
            menu_name = row.get("menu_name", "")
            if menu_name:
                recent_menus[menu_name] = recent_menus.get(menu_name, 0) + row.get("qty", 0)
        
        recent_top5 = sorted(recent_menus.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 변화 분석
        changes = []
        baseline_dict = {name: qty for name, qty in baseline_top5}
        recent_dict = {name: qty for name, qty in recent_top5}
        
        # Baseline 순위
        baseline_rank = {name: idx + 1 for idx, (name, _) in enumerate(baseline_top5)}
        
        for menu_name, recent_qty in recent_top5:
            baseline_qty = baseline_dict.get(menu_name, 0)
            rank_change = baseline_rank.get(menu_name, 999) - (recent_top5.index((menu_name, recent_qty)) + 1)
            
            qty_delta_pct = ((recent_qty - baseline_qty) / baseline_qty * 100) if baseline_qty > 0 else 0
            
            changes.append({
                "menu_name": menu_name,
                "qty_delta_pct": qty_delta_pct,
                "sales_delta_pct": qty_delta_pct,  # 간단화: 판매량 변화 = 매출 변화
                "rank_change": rank_change,
            })
        
        return changes
    except Exception:
        return []


def _classify_primary_cause(
    sales_delta: float,
    visitors_delta: float,
    avgp_delta: float,
    quantity_delta: float,
    menu_changes: List[Dict]
) -> Tuple[str, int, List[str]]:
    """
    원인 분류
    
    Returns:
        (primary_cause, confidence, evidence)
    """
    evidence = []
    confidence = 0
    
    # A. 유입 문제 (traffic)
    if visitors_delta < -10:
        evidence.append(f"네이버방문자 {visitors_delta:.1f}%")
        confidence += 40
    
    # B. 메뉴 문제 (menu)
    if quantity_delta < -10:
        evidence.append(f"총 판매량 {quantity_delta:.1f}%")
        confidence += 30
    
    # 상위 메뉴 급락
    top3_drops = [m for m in menu_changes[:3] if m.get("qty_delta_pct", 0) < -15]
    if len(top3_drops) >= 2:
        evidence.append(f"상위 메뉴 {len(top3_drops)}개 급락")
        confidence += 20
    
    # C. 가격/구조 문제 (price)
    if avgp_delta < -5:
        evidence.append(f"객단가 {avgp_delta:.1f}%")
        confidence += 25
    
    # D. 원가 구조 문제 (cost) - 간단 판단
    if sales_delta < -10 and avgp_delta > 0 and visitors_delta > -5:
        # 매출은 하락했는데 객단가는 유지/상승, 방문자는 큰 변화 없음
        # → 원가 상승 가능성
        evidence.append("객단가 유지 중 원가 상승 가능")
        confidence += 15
    
    # E. 생존선 문제 (structure) - design_state 기반 판단 필요
    # 여기서는 간단히 판단하지 않음 (외부에서 design_state와 결합)
    
    # 우선순위 결정
    if visitors_delta < -15:
        return "traffic", min(confidence, 100), evidence
    elif quantity_delta < -15 or len(top3_drops) >= 2:
        return "menu", min(confidence, 100), evidence
    elif avgp_delta < -8:
        return "price", min(confidence, 100), evidence
    elif sales_delta < -10 and avgp_delta > 0:
        return "cost", min(confidence, 100), evidence
    else:
        return "structure", min(confidence, 100), evidence
