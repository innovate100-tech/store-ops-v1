"""
전략 미션 자동 감시 및 평가 엔진
"""
from __future__ import annotations

import streamlit as st
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Optional

from src.storage_supabase import load_best_available_daily_sales


@st.cache_data(ttl=300)
def evaluate_mission_effect(mission: Dict, store_id: str) -> Optional[Dict]:
    """
    미션 효과 자동 평가
    
    Args:
        mission: 미션 dict (completed_at 포함)
        store_id: 매장 ID
    
    Returns:
        {
            "result_type": "improved" | "no_change" | "worsened" | "data_insufficient",
            "coach_comment": str,
            "baseline": {...},
            "after": {...},
            "delta": {...},
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
                if 'T' in completed_at_str:
                    completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
                else:
                    completed_at = datetime.strptime(completed_at_str, '%Y-%m-%d')
                    completed_at = completed_at.replace(tzinfo=kst)
            except Exception:
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
            return {
                "result_type": "data_insufficient",
                "coach_comment": "아직 7일이 지나지 않았어요. 데이터가 더 쌓이면 자동으로 평가합니다.",
                "baseline": {},
                "after": {},
                "delta": {},
                "after_days": after_days,
            }
        
        # Baseline: completed_date 이전 7일
        baseline_start = completed_date - timedelta(days=7)
        baseline_end = completed_date - timedelta(days=1)
        
        # After: completed_date 이후 after_days일
        after_start = completed_date + timedelta(days=1)
        after_end = completed_date + timedelta(days=after_days)
        
        # 데이터 로드
        start_date = (baseline_start - timedelta(days=2)).isoformat()
        end_date = after_end.isoformat()
        
        sales_df = load_best_available_daily_sales(
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if sales_df.empty:
            return {
                "result_type": "data_insufficient",
                "coach_comment": "데이터가 부족하여 평가할 수 없습니다.",
                "baseline": {},
                "after": {},
                "delta": {},
                "after_days": 0,
            }
        
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
            return {
                "result_type": "data_insufficient",
                "coach_comment": "비교 데이터가 부족합니다.",
                "baseline": {},
                "after": {},
                "delta": {},
                "after_days": 0,
            }
        
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
        
        # 결과 타입 분류
        result_type, coach_comment = _classify_result(sales_delta_pct, visitors_delta_pct, avgp_delta_pct, after_days)
        
        return {
            "result_type": result_type,
            "coach_comment": coach_comment,
            "baseline": {
                "sales_avg": baseline_sales,
                "visitors_avg": baseline_visitors,
                "avgp": baseline_avgp,
            },
            "after": {
                "sales_avg": after_sales,
                "visitors_avg": after_visitors,
                "avgp": after_avgp,
            },
            "delta": {
                "sales_delta_pct": sales_delta_pct,
                "visitors_delta_pct": visitors_delta_pct,
                "avgp_delta_pct": avgp_delta_pct,
            },
            "after_days": after_days,
        }
    except Exception as e:
        return None


def _classify_result(sales_delta: float, visitors_delta: float, avgp_delta: float, after_days: int) -> tuple:
    """
    결과 타입 분류 및 코치 코멘트 생성
    
    Returns:
        (result_type, coach_comment)
    """
    # improved: 매출 ↑ AND (방문자 ↑ OR 객단가 ↑)
    if sales_delta > 5 and (visitors_delta > 5 or avgp_delta > 5):
        comment = "매출이 개선되었습니다."
        if visitors_delta > 5:
            comment += " 네이버방문자 증가가 기여했습니다."
        if avgp_delta > 5:
            comment += " 객단가 개선이 기여했습니다."
        return "improved", comment
    
    # worsened: 매출 ↓ AND (방문자 ↓ OR 객단가 ↓)
    if sales_delta < -5 and (visitors_delta < -5 or avgp_delta < -5):
        comment = "매출이 더 감소했습니다."
        if visitors_delta < -5:
            comment += " 네이버방문자 감소가 원인일 수 있습니다."
        if avgp_delta < -5:
            comment += " 객단가 하락이 원인일 수 있습니다."
        comment += " 상위 구조 문제 가능성이 커졌습니다."
        return "worsened", comment
    
    # no_change: 매출 변화 ±5% 이내
    if abs(sales_delta) <= 5:
        if after_days < 7:
            comment = f"({after_days}일 기준) 변화가 미미합니다. 구조 변화가 아직 숫자에 반영되지 않았을 수 있습니다."
        else:
            comment = "변화가 미미합니다. 현재 전략의 효과가 제한적일 수 있습니다."
        return "no_change", comment
    
    # 기타: 혼재된 결과
    if sales_delta > 5:
        if visitors_delta < -5:
            comment = "매출은 증가했지만 네이버방문자가 감소했습니다. 객단가 상승이 기여했을 수 있습니다."
        elif avgp_delta < -5:
            comment = "매출은 증가했지만 객단가가 하락했습니다. 방문자 증가가 기여했을 수 있습니다."
        else:
            comment = "매출이 개선되었습니다."
        return "improved", comment
    
    if sales_delta < -5:
        if visitors_delta > 5:
            comment = "매출은 감소했지만 네이버방문자는 증가했습니다. 객단가 하락이 원인일 수 있습니다."
        elif avgp_delta > 5:
            comment = "매출은 감소했지만 객단가는 상승했습니다. 방문자 감소가 원인일 수 있습니다."
        else:
            comment = "매출이 더 감소했습니다. 상위 구조 문제 가능성이 커졌습니다."
        return "worsened", comment
    
    return "no_change", "변화가 미미합니다."
