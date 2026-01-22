"""
대시보드 컨텍스트 생성
"""
from src.utils.time_utils import current_year_kst, current_month_kst
from src.auth import get_current_store_id as _get_current_store_id


def _create_dashboard_context():
    """대시보드 공통 컨텍스트 생성"""
    store_id = _get_current_store_id() or "default"
    current_year = current_year_kst()
    current_month = current_month_kst()
    
    return {
        'store_id': store_id,
        'year': current_year,
        'month': current_month,
    }
