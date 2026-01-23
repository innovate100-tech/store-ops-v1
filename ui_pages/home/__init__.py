"""
홈 (사장 계기판) 패키지
리팩터: home_page, home_data, home_alerts, home_rules, home_components, home_lazy
"""
from ui_pages.home.home_page import (
    render_home,
    _render_home_body,
    get_coach_summary,
    get_month_status_summary,
)
from ui_pages.home.home_data import (
    get_monthly_close_stats,
    get_close_count,
    get_menu_count,
    check_actual_settlement_exists,
    detect_data_level,
    detect_owner_day_level,
)
from ui_pages.home.home_rules import get_problems_top3, get_good_points_top3
from ui_pages.home.home_alerts import get_anomaly_signals
from ui_pages.home.home_lazy import get_store_financial_structure

__all__ = [
    "render_home",
    "_render_home_body",
    "get_problems_top3",
    "get_good_points_top3",
    "get_anomaly_signals",
    "get_coach_summary",
    "get_month_status_summary",
    "get_monthly_close_stats",
    "get_close_count",
    "get_menu_count",
    "check_actual_settlement_exists",
    "detect_data_level",
    "detect_owner_day_level",
    "get_store_financial_structure",
]
