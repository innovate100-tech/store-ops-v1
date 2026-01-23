"""
설계 데이터 통합 인사이트 집계 레이어
- 설계 DB + 운영 데이터(SSOT best_available)를 함께 읽어서
  "현재 상태 요약"을 단일 dict로 반환
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

from src.storage_supabase import (
    load_csv,
    load_menu_role_tags,
    load_ingredient_structure_state,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_monthly_sales_total,
)
from src.analytics import calculate_menu_cost
from ui_pages.design_lab.menu_portfolio_helpers import (
    get_menu_portfolio_tags,
    calculate_portfolio_balance_score,
)
from ui_pages.design_lab.ingredient_structure_helpers import (
    calculate_ingredient_usage_cost,
    calculate_cost_concentration,
    identify_high_risk_ingredients,
)


@st.cache_data(ttl=300)  # 5분 캐시
def get_design_insights(store_id: str, year: int, month: int) -> dict:
    """
    설계 데이터 통합 인사이트 집계
    
    Returns:
        {
            "menu_portfolio": {...},
            "menu_profit": {...},
            "ingredient_structure": {...},
            "revenue_structure": {...}
        }
    """
    if not store_id:
        return _get_empty_insights()
    
    try:
        insights = {
            "menu_portfolio": _get_menu_portfolio_insights(store_id),
            "menu_profit": _get_menu_profit_insights(store_id),
            "ingredient_structure": _get_ingredient_structure_insights(store_id),
            "revenue_structure": _get_revenue_structure_insights(store_id, year, month),
        }
        return insights
    except Exception as e:
        # 에러 발생 시 빈 인사이트 반환
        return _get_empty_insights()


def _get_empty_insights() -> dict:
    """빈 인사이트 구조 반환"""
    return {
        "menu_portfolio": {
            "has_data": False,
            "margin_menu_count": 0,
            "role_unclassified_ratio": 0.0,
            "bait_ratio": 0.0,
            "volume_ratio": 0.0,
            "portfolio_balance_score": 0,
            "primary_issue": None,
        },
        "menu_profit": {
            "has_data": False,
            "high_cogs_ratio_menu_count": 0,
            "worst_cogs_ratio": 0.0,
            "low_contribution_menu_count": 0,
            "primary_issue": None,
        },
        "ingredient_structure": {
            "has_data": False,
            "top3_concentration": 0.0,
            "high_risk_ingredient_count": 0,
            "missing_substitute_count": 0,
            "missing_order_type_count": 0,
            "primary_issue": None,
        },
        "revenue_structure": {
            "has_data": False,
            "break_even_sales": 0.0,
            "expected_month_sales": 0.0,
            "break_even_gap_ratio": 0.0,
            "primary_issue": None,
        },
    }


def _get_menu_portfolio_insights(store_id: str) -> dict:
    """메뉴 포트폴리오 인사이트"""
    try:
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        if menu_df.empty:
            return {
                "has_data": False,
                "margin_menu_count": 0,
                "role_unclassified_ratio": 0.0,
                "bait_ratio": 0.0,
                "volume_ratio": 0.0,
                "portfolio_balance_score": 0,
                "primary_issue": None,
            }
        
        # DB에서 역할 태그 로드
        roles = get_menu_portfolio_tags(store_id)
        
        # 역할 분포 계산
        role_counts = {"미끼": 0, "볼륨": 0, "마진": 0, "미분류": 0}
        total_menus = len(menu_df)
        
        for menu_name in menu_df['메뉴명'].tolist():
            role = roles.get(menu_name, "미분류")
            if role in role_counts:
                role_counts[role] += 1
            else:
                role_counts["미분류"] += 1
        
        margin_menu_count = role_counts["마진"]
        bait_ratio = (role_counts["미끼"] / total_menus * 100) if total_menus > 0 else 0.0
        volume_ratio = (role_counts["볼륨"] / total_menus * 100) if total_menus > 0 else 0.0
        role_unclassified_ratio = (role_counts["미분류"] / total_menus * 100) if total_menus > 0 else 0.0
        
        # 포트폴리오 균형 점수 계산
        from ui_pages.design_lab.menu_portfolio_helpers import get_menu_portfolio_categories
        categories = get_menu_portfolio_categories(store_id)
        balance_score, _ = calculate_portfolio_balance_score(menu_df, roles, categories)
        
        # Primary issue 판단
        primary_issue = None
        if margin_menu_count == 0 and total_menus >= 3:
            primary_issue = "MARGIN_ZERO"
        elif role_unclassified_ratio >= 30.0:
            primary_issue = "UNCLASSIFIED_HIGH"
        elif bait_ratio >= 50.0:
            primary_issue = "BAIT_EXCESS"
        elif balance_score < 40:
            primary_issue = "BALANCE_POOR"
        
        return {
            "has_data": True,
            "margin_menu_count": margin_menu_count,
            "role_unclassified_ratio": role_unclassified_ratio,
            "bait_ratio": bait_ratio,
            "volume_ratio": volume_ratio,
            "portfolio_balance_score": balance_score,
            "primary_issue": primary_issue,
        }
    except Exception:
        return {
            "has_data": False,
            "margin_menu_count": 0,
            "role_unclassified_ratio": 0.0,
            "bait_ratio": 0.0,
            "volume_ratio": 0.0,
            "portfolio_balance_score": 0,
            "primary_issue": None,
        }


def _get_menu_profit_insights(store_id: str) -> dict:
    """메뉴 수익 구조 인사이트"""
    try:
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단가'])
        
        if menu_df.empty or recipe_df.empty or ingredient_df.empty:
            return {
                "has_data": False,
                "high_cogs_ratio_menu_count": 0,
                "worst_cogs_ratio": 0.0,
                "low_contribution_menu_count": 0,
                "primary_issue": None,
            }
        
        # 원가 계산
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        if cost_df.empty:
            return {
                "has_data": False,
                "high_cogs_ratio_menu_count": 0,
                "worst_cogs_ratio": 0.0,
                "low_contribution_menu_count": 0,
                "primary_issue": None,
            }
        
        # 고원가율 메뉴 (35% 이상)
        high_cogs_menus = cost_df[cost_df['원가율'] >= 35]
        high_cogs_ratio_menu_count = len(high_cogs_menus)
        
        # 최악 원가율
        worst_cogs_ratio = cost_df['원가율'].max() if not cost_df.empty else 0.0
        
        # 저공헌이익 메뉴 (공헌이익 < 판매가의 20%)
        if '원가' in cost_df.columns and '판매가' in cost_df.columns:
            cost_df['공헌이익'] = cost_df['판매가'] - cost_df['원가']
            cost_df['공헌이익률'] = (cost_df['공헌이익'] / cost_df['판매가'] * 100).fillna(0)
            low_contribution_menus = cost_df[cost_df['공헌이익률'] < 20]
            low_contribution_menu_count = len(low_contribution_menus)
        else:
            low_contribution_menu_count = 0
        
        # Primary issue 판단
        primary_issue = None
        if worst_cogs_ratio >= 50.0:
            primary_issue = "COGS_VERY_HIGH"
        elif high_cogs_ratio_menu_count >= 3:
            primary_issue = "COGS_HIGH_COUNT"
        elif low_contribution_menu_count >= 3:
            primary_issue = "CONTRIBUTION_LOW"
        
        return {
            "has_data": True,
            "high_cogs_ratio_menu_count": high_cogs_ratio_menu_count,
            "worst_cogs_ratio": worst_cogs_ratio,
            "low_contribution_menu_count": low_contribution_menu_count,
            "primary_issue": primary_issue,
        }
    except Exception:
        return {
            "has_data": False,
            "high_cogs_ratio_menu_count": 0,
            "worst_cogs_ratio": 0.0,
            "low_contribution_menu_count": 0,
            "primary_issue": None,
        }


def _get_ingredient_structure_insights(store_id: str) -> dict:
    """재료 구조 인사이트"""
    try:
        # 재료 사용량 계산
        ingredient_usage_df = calculate_ingredient_usage_cost(store_id)
        if ingredient_usage_df.empty:
            return {
                "has_data": False,
                "top3_concentration": 0.0,
                "high_risk_ingredient_count": 0,
                "missing_substitute_count": 0,
                "missing_order_type_count": 0,
                "primary_issue": None,
            }
        
        # TOP3 집중도 계산
        top3_concentration_pct, _ = calculate_cost_concentration(ingredient_usage_df)
        top3_concentration = top3_concentration_pct / 100.0  # 0~1로 변환
        
        # 고위험 재료 판별
        high_risk_df = identify_high_risk_ingredients(ingredient_usage_df, cost_threshold=20.0, menu_threshold=3)
        high_risk_ingredient_count = len(high_risk_df) if not high_risk_df.empty else 0
        
        # DB에서 재료 설계 상태 로드
        db_states = load_ingredient_structure_state(store_id)
        
        # 재료명 -> ingredient_id 매핑
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
        ingredient_id_map = {}
        ingredient_name_map = {}  # id -> name
        if not ingredient_df.empty and 'id' in ingredient_df.columns:
            for _, row in ingredient_df.iterrows():
                ingredient_name = row.get('재료명', '')
                ingredient_id = row.get('id', '')
                if ingredient_name and ingredient_id:
                    ingredient_id_map[ingredient_name] = ingredient_id
                    ingredient_name_map[ingredient_id] = ingredient_name
        
        # 대체재/발주유형 미설정 개수 계산
        missing_substitute_count = 0
        missing_order_type_count = 0
        
        for ingredient_name in ingredient_usage_df['재료명'].tolist():
            ingredient_id = ingredient_id_map.get(ingredient_name)
            if ingredient_id:
                state = db_states.get(ingredient_id, {})
                if state.get('is_substitutable') is None:
                    missing_substitute_count += 1
                if state.get('order_type') in (None, 'unset'):
                    missing_order_type_count += 1
        
        # Primary issue 판단
        primary_issue = None
        if top3_concentration >= 0.70 and missing_substitute_count > 0:
            primary_issue = "CONCENTRATION_HIGH_NO_SUBSTITUTE"
        elif top3_concentration >= 0.70:
            primary_issue = "CONCENTRATION_HIGH"
        elif high_risk_ingredient_count > 0 and missing_substitute_count > 0:
            primary_issue = "HIGH_RISK_NO_SUBSTITUTE"
        elif missing_order_type_count >= 3:
            primary_issue = "ORDER_TYPE_MISSING"
        
        return {
            "has_data": True,
            "top3_concentration": top3_concentration,
            "high_risk_ingredient_count": high_risk_ingredient_count,
            "missing_substitute_count": missing_substitute_count,
            "missing_order_type_count": missing_order_type_count,
            "primary_issue": primary_issue,
        }
    except Exception:
        return {
            "has_data": False,
            "top3_concentration": 0.0,
            "high_risk_ingredient_count": 0,
            "missing_substitute_count": 0,
            "missing_order_type_count": 0,
            "primary_issue": None,
        }


def _get_revenue_structure_insights(store_id: str, year: int, month: int) -> dict:
    """수익 구조 인사이트"""
    try:
        # 손익분기점 계산
        break_even = calculate_break_even_sales(store_id, year, month)
        if break_even <= 0:
            return {
                "has_data": False,
                "break_even_sales": 0.0,
                "expected_month_sales": 0.0,
                "break_even_gap_ratio": 0.0,
                "primary_issue": None,
            }
        
        # 예상 매출 계산 (간단: 월 누적 / 경과일수 * 월 총일수)
        monthly_sales = load_monthly_sales_total(store_id, year, month)
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        
        if now.year == year and now.month == month:
            days_passed = now.day
            days_in_month = 30  # 간단 추정
            if days_passed > 0:
                expected_month_sales = (monthly_sales / days_passed) * days_in_month
            else:
                expected_month_sales = monthly_sales
        else:
            expected_month_sales = monthly_sales
        
        # 손익분기점 대비 비율
        break_even_gap_ratio = (expected_month_sales / break_even) if break_even > 0 else 0.0
        
        # Primary issue 판단
        primary_issue = None
        if break_even_gap_ratio < 0.8:
            primary_issue = "BREAK_EVEN_GAP_LARGE"
        elif break_even_gap_ratio < 1.0:
            primary_issue = "BREAK_EVEN_BELOW"
        
        return {
            "has_data": True,
            "break_even_sales": break_even,
            "expected_month_sales": expected_month_sales,
            "break_even_gap_ratio": break_even_gap_ratio,
            "primary_issue": primary_issue,
        }
    except Exception:
        return {
            "has_data": False,
            "break_even_sales": 0.0,
            "expected_month_sales": 0.0,
            "break_even_gap_ratio": 0.0,
            "primary_issue": None,
        }
