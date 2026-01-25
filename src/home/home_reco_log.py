"""
홈 추천 이벤트 로깅 모듈
추천 표시(shown) 및 클릭(clicked) 이벤트 저장
"""
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Tuple

from src.storage_supabase import get_read_client, get_supabase_client
from src.utils.time_utils import today_kst

logger = logging.getLogger(__name__)


def log_reco_event(
    user_id: str,
    store_id: str,
    reco_dict: dict,
    event_type: str,
    tz: str = "Asia/Seoul"
) -> bool:
    """
    추천 이벤트 로깅 (shown 또는 clicked)
    
    Args:
        user_id: 사용자 ID
        store_id: 매장 ID
        reco_dict: 추천 엔진 결과 dict (type, message, action_page, status 포함)
        event_type: 'shown' 또는 'clicked'
        tz: 타임존 (기본값: Asia/Seoul)
    
    Returns:
        bool: 저장 성공 여부
    """
    if event_type not in ('shown', 'clicked'):
        logger.warning(f"Invalid event_type: {event_type}")
        return False
    
    try:
        if not user_id or not store_id:
            return False
        
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # snapshot 생성 (status 정보 포함)
        status = reco_dict.get("status", {})
        snapshot = {
            "yesterday_closed": status.get("yesterday_closed", False),
            "last7_close_days": status.get("last7_close_days", 0),
            "recipe_cover_rate": status.get("recipe_cover_rate", 0.0),
            "sales_goal_exists": status.get("sales_goal_exists", False),
            "cost_goal_exists": status.get("cost_goal_exists", False),
            "close_count": status.get("close_count", 0),
            "menu_count": status.get("menu_count", 0),
            "target_count": status.get("target_count", 0)
        }
        
        # 메시지 (너무 길면 잘라내기)
        message = reco_dict.get("message", "")
        if message and len(message) > 200:
            message = message[:197] + "..."
        
        # 이벤트 저장
        event_data = {
            "user_id": user_id,
            "store_id": store_id,
            "event_type": event_type,
            "reco_type": reco_dict.get("type", "UNKNOWN"),
            "action_page": reco_dict.get("action_page"),
            "message": message,
            "snapshot": snapshot
        }
        
        result = supabase.table("home_reco_events").insert(event_data).execute()
        
        if result.data:
            logger.debug(f"Reco event logged: {event_type}, type={reco_dict.get('type')}")
            return True
        else:
            logger.warning(f"Failed to log reco event: no data returned")
            return False
    
    except Exception as e:
        # 중복 제약 위반은 정상 (하루 1회 제한)
        error_msg = str(e).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            logger.debug(f"Reco event already logged today (duplicate): {event_type}")
            return True  # 중복은 성공으로 처리
        
        logger.warning(f"Failed to log reco event: {e}")
        return False


def get_reco_weekly_counts(store_id: str, days: int = 7, tz: str = "Asia/Seoul") -> Tuple[int, int]:
    """
    최근 N일간 추천 이벤트 집계
    
    Args:
        store_id: 매장 ID
        days: 집계 기간 (기본값: 7일)
        tz: 타임존 (기본값: Asia/Seoul)
    
    Returns:
        tuple: (shown_count, clicked_count)
    """
    try:
        if not store_id:
            return (0, 0)
        
        supabase = get_read_client()
        if not supabase:
            return (0, 0)
        
        # 최근 N일 기준 날짜 계산
        tz_obj = ZoneInfo(tz)
        from datetime import datetime
        cutoff_time = datetime.now(tz_obj) - timedelta(days=days)
        
        # shown 집계
        try:
            shown_result = supabase.table("home_reco_events")\
                .select("id", count="exact")\
                .eq("store_id", store_id)\
                .eq("event_type", "shown")\
                .gte("event_at", cutoff_time.isoformat())\
                .execute()
            shown_count = shown_result.count if hasattr(shown_result, 'count') and shown_result.count is not None else 0
        except Exception as e:
            logger.warning(f"Failed to count shown events: {e}")
            shown_count = 0
        
        # clicked 집계
        try:
            clicked_result = supabase.table("home_reco_events")\
                .select("id", count="exact")\
                .eq("store_id", store_id)\
                .eq("event_type", "clicked")\
                .gte("event_at", cutoff_time.isoformat())\
                .execute()
            clicked_count = clicked_result.count if hasattr(clicked_result, 'count') and clicked_result.count is not None else 0
        except Exception as e:
            logger.warning(f"Failed to count clicked events: {e}")
            clicked_count = 0
        
        return (shown_count, clicked_count)
    
    except Exception as e:
        logger.warning(f"Failed to get reco weekly counts: {e}")
        return (0, 0)
