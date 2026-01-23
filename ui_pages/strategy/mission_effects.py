"""
전략 실행 미션 효과 비교 (7일 후)
"""
from __future__ import annotations

import streamlit as st
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Optional

from src.storage_supabase import load_best_available_daily_sales


@st.cache_data(ttl=300)
def compute_mission_effect(mission: Dict, store_id: str) -> Optional[Dict]:
    """
    7일 후 효과 비교 계산
    
    Args:
        mission: 미션 dict (completed_at 포함)
        store_id: 매장 ID
    
    Returns:
        {
            "sales_delta_pct": float,
            "visitors_delta_pct": float,
            "avgp_delta_pct": float,
            "interpretation": str,
        } 또는 None
    """
    if not mission or not store_id:
        return None
    
    try:
        completed_at_str = mission.get("completed_at")
        if not completed_at_str:
            return None
        
        # completed_at 파싱
        kst = ZoneInfo("Asia/Seoul")
        if isinstance(completed_at_str, str):
            try:
                # ISO 형식 파싱
                if 'T' in completed_at_str:
                    completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
                else:
                    # 날짜만 있는 경우
                    completed_at = datetime.strptime(completed_at_str, '%Y-%m-%d')
                    completed_at = completed_at.replace(tzinfo=kst)
            except Exception:
                # 파싱 실패 시 오늘로 fallback
                completed_at = datetime.now(kst)
        else:
            completed_at = completed_at_str
        
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=kst)
        else:
            completed_at = completed_at.astimezone(kst)
        
        completed_date = completed_at.date()
        today = datetime.now(kst).date()
        
        # 7일 후 데이터가 있는지 확인
        days_passed = (today - completed_date).days
        if days_passed < 3:
            # 최소 3일 데이터라도 있으면 임시 계산
            after_days = min(days_passed, 7)
        elif days_passed >= 7:
            after_days = 7
        else:
            # 3~6일 사이면 부분 구간으로 계산
            after_days = days_passed
        
        if after_days < 3:
            return None  # 데이터 부족
        
        # Baseline: completed_date 이전 7일
        baseline_start = completed_date - timedelta(days=7)
        baseline_end = completed_date - timedelta(days=1)
        
        # After: completed_date 이후 after_days일
        after_start = completed_date + timedelta(days=1)
        after_end = completed_date + timedelta(days=after_days)
        
        # 데이터 로드
        start_date = (baseline_start - timedelta(days=2)).isoformat()  # 여유분
        end_date = after_end.isoformat()
        
        sales_df = load_best_available_daily_sales(
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if sales_df.empty:
            return None
        
        sales_df['date'] = sales_df['date'].apply(lambda x: x.date() if isinstance(x, datetime) else x)
        
        # Baseline 계산
        baseline_df = sales_df[
            (sales_df['date'] >= baseline_start) &
            (sales_df['date'] <= baseline_end)
        ]
        
        # After 계산
        after_df = sales_df[
            (sales_df['date'] >= after_start) &
            (sales_df['date'] <= after_end)
        ]
        
        if baseline_df.empty or after_df.empty:
            return None
        
        # 평균 계산
        baseline_sales = baseline_df['total_sales'].mean() if 'total_sales' in baseline_df.columns else 0
        after_sales = after_df['total_sales'].mean() if 'total_sales' in after_df.columns else 0
        
        baseline_visitors = baseline_df['visitors'].mean() if 'visitors' in baseline_df.columns else 0
        after_visitors = after_df['visitors'].mean() if 'visitors' in after_df.columns else 0
        
        baseline_avgp = (baseline_sales / baseline_visitors) if baseline_visitors > 0 else 0
        after_avgp = (after_sales / after_visitors) if after_visitors > 0 else 0
        
        # 변화율 계산
        sales_delta_pct = ((after_sales - baseline_sales) / baseline_sales * 100) if baseline_sales > 0 else 0
        visitors_delta_pct = ((after_visitors - baseline_visitors) / baseline_visitors * 100) if baseline_visitors > 0 else 0
        avgp_delta_pct = ((after_avgp - baseline_avgp) / baseline_avgp * 100) if baseline_avgp > 0 else 0
        
        # 해석 생성
        interpretation = _generate_interpretation(sales_delta_pct, visitors_delta_pct, avgp_delta_pct, after_days)
        
        return {
            "sales_delta_pct": sales_delta_pct,
            "visitors_delta_pct": visitors_delta_pct,
            "avgp_delta_pct": avgp_delta_pct,
            "interpretation": interpretation,
            "after_days": after_days,
        }
    except Exception as e:
        return None


def _generate_interpretation(sales_delta: float, visitors_delta: float, avgp_delta: float, after_days: int) -> str:
    """효과 해석 생성"""
    parts = []
    
    if visitors_delta > 5:
        parts.append("네이버방문자가 회복되었습니다")
    elif visitors_delta < -5:
        parts.append("네이버방문자가 더 감소했습니다")
    
    if avgp_delta > 5:
        parts.append("객단가가 개선되었습니다")
    elif avgp_delta < -5:
        parts.append("객단가가 더 하락했습니다")
    
    if sales_delta > 5:
        parts.append("매출이 회복되었습니다")
    elif sales_delta < -5:
        parts.append("매출이 더 감소했습니다")
    
    if not parts:
        return "변화가 미미합니다. 추가 조치가 필요할 수 있습니다."
    
    if after_days < 7:
        return f"({after_days}일 기준) " + " / ".join(parts) + "."
    else:
        return " / ".join(parts) + "."
