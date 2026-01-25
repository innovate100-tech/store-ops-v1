"""
홈 화면 추천 엔진 v1
규칙 기반 자동 추천 (AI 금지)
"""
import logging
import pandas as pd
from datetime import timedelta
from zoneinfo import ZoneInfo

from src.storage_supabase import get_day_record_status, get_read_client, load_csv
from src.utils.time_utils import today_kst, current_year_kst, current_month_kst
from src.ui_helpers import safe_resp_first_data

logger = logging.getLogger(__name__)


def get_home_recommendation_v1(user_id: str, store_id: str, tz: str = "Asia/Seoul") -> dict:
    """
    홈 화면 추천 엔진 v1
    
    판정 순서:
    0) 신규 사용자 여부
    1) 어제 마감 여부 (최우선 운영 게이트)
    2) 최근 7일 마감 습관 (7/7 아니면 여기서 종료)
    3) 레시피 커버율 70% 기준
    4) 목표(매출 + 비용) 둘 다 있어야 통과
    
    Args:
        user_id: 사용자 ID
        store_id: 매장 ID
        tz: 타임존 (기본값: Asia/Seoul)
    
    Returns:
        dict: {
            "type": "TYPE_0" | "TYPE_1-A" | "TYPE_1-B" | "TYPE_2" | "TYPE_3" | "TYPE_4",
            "status": {
                "yesterday_closed": bool,
                "last7_close_days": int,
                "recipe_cover_rate": float,
                "sales_goal_exists": bool,
                "cost_goal_exists": bool,
                "close_count": int,
                "menu_count": int,
                "target_count": int
            },
            "message": str,
            "action_label": str,
            "action_page": str
        }
    """
    # 기본값 (안전 가드)
    default_result = {
        "type": "TYPE_0",
        "status": {
            "yesterday_closed": False,
            "last7_close_days": 0,
            "recipe_cover_rate": 0.0,
            "sales_goal_exists": False,
            "cost_goal_exists": False,
            "close_count": 0,
            "menu_count": 0,
            "target_count": 0
        },
        "message": "상태 계산 중입니다.",
        "action_label": "오늘 마감 시작하기",
        "action_page": "일일 입력(통합)"
    }
    
    try:
        if not store_id:
            return default_result
        
        supabase = get_read_client()
        if not supabase:
            return default_result
        
        # 타임존 설정
        tz_obj = ZoneInfo(tz)
        today = today_kst()
        yesterday = today - timedelta(days=1)
        current_year = current_year_kst()
        current_month = current_month_kst()
        
        # ============================================
        # 데이터 수집 (안전 가드 포함)
        # ============================================
        
        # A) 신규 여부 판단: 마감 0건, 메뉴 0건, 목표 0건
        try:
            close_count_result = supabase.table("daily_close")\
                .select("id", count="exact")\
                .eq("store_id", store_id)\
                .execute()
            close_count = close_count_result.count if hasattr(close_count_result, 'count') and close_count_result.count is not None else 0
        except Exception as e:
            logger.warning(f"Failed to get close count: {e}")
            close_count = 0
        
        try:
            menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'], store_id=store_id)
            menu_count = len(menu_df) if not menu_df.empty else 0
        except Exception as e:
            logger.warning(f"Failed to get menu count: {e}")
            menu_count = 0
        
        try:
            targets_df = load_csv('targets.csv', default_columns=[
                '연도', '월', '목표매출', '목표원가율'
            ], store_id=store_id)
            target_count = len(targets_df) if not targets_df.empty else 0
        except Exception as e:
            logger.warning(f"Failed to get target count: {e}")
            target_count = 0
            targets_df = pd.DataFrame()  # 빈 DataFrame으로 초기화
        
        # TYPE 0: 신규 사용자 판단
        if close_count == 0 and menu_count == 0 and target_count == 0:
            return {
                "type": "TYPE_0",
                "status": {
                    "yesterday_closed": False,
                    "last7_close_days": 0,
                    "recipe_cover_rate": 0.0,
                    "sales_goal_exists": False,
                    "cost_goal_exists": False,
                    "close_count": close_count,
                    "menu_count": menu_count,
                    "target_count": target_count
                },
                "message": """👋 환영합니다.
이 앱은 매장을 숫자로 만드는 시스템입니다.

여기서는 매출을 '느끼는 것'이 아니라,
보고, 이해하고, 바꾸는 방식으로 장사하게 됩니다.

👉 첫 단계는 아주 단순합니다.
오늘 마감부터 입력해 보세요.

마감이 쌓이면, 이 앱은 당신 매장을 분석하고, 방향을 제시하기 시작합니다.""",
                "action_label": "오늘 마감 시작하기",
                "action_page": "일일 입력(통합)"
            }
        
        # B) 어제 마감 여부
        try:
            yesterday_status = get_day_record_status(store_id, yesterday)
            yesterday_closed = yesterday_status.get("has_close", False)
        except Exception as e:
            logger.warning(f"Failed to get yesterday status: {e}")
            yesterday_closed = False
        
        # TYPE 1-A: 어제 마감 안 함
        if not yesterday_closed:
            return {
                "type": "TYPE_1-A",
                "status": {
                    "yesterday_closed": False,
                    "last7_close_days": 0,
                    "recipe_cover_rate": 0.0,
                    "sales_goal_exists": False,
                    "cost_goal_exists": False,
                    "close_count": close_count,
                    "menu_count": menu_count,
                    "target_count": target_count
                },
                "message": """🎯 어제 마감을 하지 않았습니다.
마감이 없으면, 이 앱은 아무 의미가 없습니다.""",
                "action_label": "어제 마감 입력하기",
                "action_page": "일일 입력(통합)"
            }
        
        # C) 최근 7일 마감 습관
        try:
            last7_dates = [today - timedelta(days=i) for i in range(7)]
            last7_close_days = 0
            for check_date in last7_dates:
                try:
                    status = get_day_record_status(store_id, check_date)
                    if status.get("has_close", False):
                        last7_close_days += 1
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to get last7 close days: {e}")
            last7_close_days = 0
        
        # TYPE 1-B: 마감 습관 미완성
        if last7_close_days < 7:
            return {
                "type": "TYPE_1-B",
                "status": {
                    "yesterday_closed": True,
                    "last7_close_days": last7_close_days,
                    "recipe_cover_rate": 0.0,
                    "sales_goal_exists": False,
                    "cost_goal_exists": False,
                    "close_count": close_count,
                    "menu_count": menu_count,
                    "target_count": target_count
                },
                "message": """🎯 마감이 아직 '습관'이 되지 않았습니다.
이 앱은 매일 마감하는 사장을 위한 시스템입니다.""",
                "action_label": "마감 기록 확인하기",
                "action_page": "일일 입력(통합)"
            }
        
        # D) 레시피 커버율
        try:
            recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'], store_id=store_id)
            
            if menu_count > 0 and not recipe_df.empty:
                menus_with_recipe = recipe_df['메뉴명'].nunique()
                recipe_cover_rate = menus_with_recipe / menu_count
            else:
                recipe_cover_rate = 0.0
        except Exception as e:
            logger.warning(f"Failed to calculate recipe cover rate: {e}")
            recipe_cover_rate = 0.0
        
        # TYPE 2: 레시피 구조 부족
        if recipe_cover_rate < 0.7:
            return {
                "type": "TYPE_2",
                "status": {
                    "yesterday_closed": True,
                    "last7_close_days": last7_close_days,
                    "recipe_cover_rate": recipe_cover_rate,
                    "sales_goal_exists": False,
                    "cost_goal_exists": False,
                    "close_count": close_count,
                    "menu_count": menu_count,
                    "target_count": target_count
                },
                "message": """🎯 지금 매장은 돌아가고 있지만, 시스템은 아닙니다.
레시피가 있어야 매출이 구조가 됩니다.""",
                "action_label": "레시피 완성하기",
                "action_page": "레시피 등록"
            }
        
        # E) 목표 존재 여부
        try:
            # targets_df가 이미 로드되어 있음
            if not targets_df.empty:
                current_target = targets_df[
                    (targets_df['연도'] == current_year) & 
                    (targets_df['월'] == current_month)
                ]
            else:
                current_target = pd.DataFrame()
            
            sales_goal_exists = False
            cost_goal_exists = False
            
            if not current_target.empty:
                from src.ui_helpers import safe_get_value
                target_sales = safe_get_value(current_target, '목표매출', 0)
                target_cost_rate = safe_get_value(current_target, '목표원가율', 0)
                
                sales_goal_exists = target_sales is not None and float(target_sales or 0) > 0
                cost_goal_exists = target_cost_rate is not None and float(target_cost_rate or 0) > 0
        except Exception as e:
            logger.warning(f"Failed to check goals: {e}")
            sales_goal_exists = False
            cost_goal_exists = False
        
        # TYPE 3: 목표 없음
        if not sales_goal_exists or not cost_goal_exists:
            return {
                "type": "TYPE_3",
                "status": {
                    "yesterday_closed": True,
                    "last7_close_days": last7_close_days,
                    "recipe_cover_rate": recipe_cover_rate,
                    "sales_goal_exists": sales_goal_exists,
                    "cost_goal_exists": cost_goal_exists,
                    "close_count": close_count,
                    "menu_count": menu_count,
                    "target_count": target_count
                },
                "message": """🎯 이제부터는 운영이 아니라, 경영 단계입니다.
목표가 없으면 모든 숫자는 그냥 기록입니다.""",
                "action_label": "이번 달 목표 설정하기",
                "action_page": "목표 매출구조"  # 또는 "목표 비용구조"
            }
        
        # TYPE 4: 모두 통과
        return {
            "type": "TYPE_4",
            "status": {
                "yesterday_closed": True,
                "last7_close_days": last7_close_days,
                "recipe_cover_rate": recipe_cover_rate,
                "sales_goal_exists": True,
                "cost_goal_exists": True,
                "close_count": close_count,
                "menu_count": menu_count,
                "target_count": target_count
            },
            "message": """🎯 이제 매장은 관리가 아니라, 개선 단계입니다.
지금부터는 숫자를 보고 바꿀 차례입니다.""",
            "action_label": "전략 센터 열기",
            "action_page": "가게 전략 센터"
        }
    
    except Exception as e:
        logger.error(f"Error in get_home_recommendation_v1: {e}", exc_info=True)
        return default_result
