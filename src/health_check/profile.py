"""
건강검진 프로필 로더
최근 건강검진 결과를 전략 엔진에서 사용할 수 있는 형태로 로드
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.auth import get_supabase_client
from src.health_check.storage import get_health_session, get_health_results

logger = logging.getLogger(__name__)


def load_latest_health_profile(store_id: str, lookback_days: int = 60) -> Dict:
    """
    최근 건강검진 프로필 로드
    
    Args:
        store_id: 매장 ID
        lookback_days: 조회 기간 (일, 기본 60일)
    
    Returns:
        {
            "exists": True/False,
            "session_id": ...,
            "completed_at": ...,
            "overall_score": float,
            "overall_grade": str,
            "main_bottleneck": str,
            "category_scores": {"Q":72.3, "S":55.0, ...},
            "risk_levels": {"Q":"yellow","F":"red", ...},
            "risk_top": ["F","H","M"],   # score 낮은 순 3개
            "strength_top": ["C","P2"],  # score 높은 순 2개
            "age_days": int,
        }
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return _get_empty_profile()
        
        # 최근 완료된 세션 조회
        cutoff_date = (datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=lookback_days)).isoformat()
        
        result = supabase.table("health_check_sessions").select("*").eq(
            "store_id", store_id
        ).not_.is_("completed_at", "null").gte(
            "completed_at", cutoff_date
        ).order("completed_at", desc=True).limit(1).execute()
        
        if not result.data or len(result.data) == 0:
            return _get_empty_profile()
        
        session = result.data[0]
        session_id = session['id']
        completed_at = session.get('completed_at')
        
        # 결과 조회
        results = get_health_results(session_id)
        if not results:
            return _get_empty_profile()
        
        # 카테고리별 점수/리스크 정리
        category_scores = {}
        risk_levels = {}
        
        for r in results:
            category = r['category']
            category_scores[category] = float(r.get('score_avg', 0))
            risk_levels[category] = r.get('risk_level', 'unknown')
        
        # risk_top: 점수가 낮은 순 3개
        if category_scores:
            risk_top = sorted(
                category_scores.items(),
                key=lambda x: x[1]
            )[:3]
            risk_top = [cat for cat, _ in risk_top]
        else:
            risk_top = []
        
        # strength_top: 점수가 높은 순 2개
        if category_scores:
            strength_top = sorted(
                category_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:2]
            strength_top = [cat for cat, _ in strength_top]
        else:
            strength_top = []
        
        # age_days 계산
        age_days = 0
        if completed_at:
            try:
                completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                now = datetime.now(ZoneInfo("Asia/Seoul"))
                age_days = (now - completed_dt.replace(tzinfo=ZoneInfo("Asia/Seoul"))).days
            except Exception:
                age_days = 999  # 파싱 실패 시 오래된 것으로 간주
        
        return {
            "exists": True,
            "session_id": session_id,
            "completed_at": completed_at,
            "overall_score": float(session.get('overall_score', 0)),
            "overall_grade": session.get('overall_grade', 'E'),
            "main_bottleneck": session.get('main_bottleneck'),
            "category_scores": category_scores,
            "risk_levels": risk_levels,
            "risk_top": risk_top,
            "strength_top": strength_top,
            "age_days": age_days
        }
    
    except Exception as e:
        logger.error(f"load_latest_health_profile: Error - {e}")
        return _get_empty_profile()


def _get_empty_profile() -> Dict:
    """빈 프로필 반환"""
    return {
        "exists": False,
        "session_id": None,
        "completed_at": None,
        "overall_score": 0.0,
        "overall_grade": "E",
        "main_bottleneck": None,
        "category_scores": {},
        "risk_levels": {},
        "risk_top": [],
        "strength_top": [],
        "age_days": 999
    }
