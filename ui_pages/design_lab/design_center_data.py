"""
가게 설계 센터 통합 진단 데이터
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st

from src.storage_supabase import (
    load_csv,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_monthly_sales_total,
)
from src.analytics import calculate_menu_cost
from src.auth import get_current_store_id
from ui_pages.design_lab.design_lab_coach_data import (
    get_menu_design_coach_data,
    get_ingredient_design_coach_data,
    get_menu_profit_design_coach_data,
    get_revenue_structure_design_coach_data,
)
from ui_pages.design_lab.menu_portfolio_helpers import (
    get_menu_portfolio_tags,
    get_menu_portfolio_categories,
    calculate_portfolio_balance_score,
)
from ui_pages.design_lab.ingredient_structure_helpers import (
    calculate_ingredient_usage_cost,
    calculate_cost_concentration,
    identify_high_risk_ingredients,
    check_order_structure_status,
)
from typing import Tuple


def get_design_center_summary(store_id: str) -> dict:
    """
    가게 설계 센터 통합 요약 데이터
    
    Returns:
        {
            "menu_portfolio": {...},
            "menu_profit": {...},
            "ingredient_structure": {...},
            "revenue_structure": {...}
        }
    """
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    year = now.year
    month = now.month
    
    summary = {
        "menu_portfolio": _get_menu_portfolio_summary(store_id),
        "menu_profit": _get_menu_profit_summary(store_id),
        "ingredient_structure": _get_ingredient_structure_summary(store_id),
        "revenue_structure": _get_revenue_structure_summary(store_id, year, month),
    }
    
    return summary


def _get_menu_portfolio_summary(store_id: str) -> dict:
    """메뉴 포트폴리오 요약"""
    try:
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        roles = get_menu_portfolio_tags(store_id)
        categories = get_menu_portfolio_categories(store_id)
        
        if menu_df.empty:
            return {
                "status": "위험",
                "score": 0,
                "menu_count": 0,
                "balance_score": 0,
                "unclassified_ratio": 100.0,
                "message": "메뉴가 등록되지 않았습니다"
            }
        
        balance_score, balance_status = calculate_portfolio_balance_score(menu_df, roles, categories)
        
        # 미분류 비율 계산
        total_menus = len(menu_df)
        unclassified_count = 0
        for menu_name in menu_df['메뉴명'].tolist():
            role = roles.get(menu_name, "미분류")
            category = categories.get(menu_name, "기타메뉴")
            if role == "미분류" or category == "기타메뉴":
                unclassified_count += 1
        
        unclassified_ratio = (unclassified_count / total_menus * 100) if total_menus > 0 else 0.0
        
        return {
            "status": balance_status,
            "score": balance_score,
            "menu_count": total_menus,
            "balance_score": balance_score,
            "unclassified_ratio": unclassified_ratio,
            "message": f"포트폴리오 균형 점수 {balance_score}점 ({balance_status})"
        }
    except Exception as e:
        return {
            "status": "위험",
            "score": 0,
            "menu_count": 0,
            "balance_score": 0,
            "unclassified_ratio": 100.0,
            "message": f"데이터 로드 실패: {e}"
        }


def _get_menu_profit_summary(store_id: str) -> dict:
    """메뉴 수익 구조 요약"""
    try:
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단가'])
        
        if menu_df.empty or recipe_df.empty or ingredient_df.empty:
            return {
                "status": "위험",
                "score": 0,
                "high_cost_rate_count": 0,
                "avg_contribution": 0,
                "message": "메뉴/레시피/재료 데이터 부족"
            }
        
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        if cost_df.empty:
            return {
                "status": "위험",
                "score": 0,
                "high_cost_rate_count": 0,
                "avg_contribution": 0,
                "message": "원가 계산 실패"
            }
        
        # 고원가율 메뉴 수 (35% 이상)
        if '원가율' in cost_df.columns:
            high_cost_count = len(cost_df[cost_df['원가율'] >= 35])
        else:
            high_cost_count = 0
        
        # 평균 공헌이익
        if '원가' in cost_df.columns and '판매가' in cost_df.columns:
            cost_df['공헌이익'] = cost_df['판매가'] - cost_df['원가']
            avg_contribution = cost_df['공헌이익'].mean()
        else:
            avg_contribution = 0
        
        # 점수 계산 (간단 룰)
        score = 100
        if high_cost_count > len(cost_df) * 0.3:  # 30% 이상 고원가율
            score -= 30
        if avg_contribution < 5000:  # 평균 공헌이익 낮음
            score -= 20
        
        status = "안정" if score >= 70 else "주의" if score >= 40 else "위험"
        
        return {
            "status": status,
            "score": max(0, min(100, score)),
            "high_cost_rate_count": high_cost_count,
            "avg_contribution": avg_contribution,
            "message": f"고원가율 메뉴 {high_cost_count}개, 평균 공헌이익 {int(avg_contribution):,}원"
        }
    except Exception as e:
        return {
            "status": "위험",
            "score": 0,
            "high_cost_rate_count": 0,
            "avg_contribution": 0,
            "message": f"데이터 로드 실패: {e}"
        }


def _get_ingredient_structure_summary(store_id: str) -> dict:
    """재료 구조 요약"""
    try:
        ingredient_usage_df = calculate_ingredient_usage_cost(store_id)
        
        if ingredient_usage_df.empty:
            return {
                "status": "위험",
                "score": 0,
                "top3_concentration": 0.0,
                "high_risk_count": 0,
                "message": "재료 사용 데이터 없음"
            }
        
        top3_concentration, top5_concentration = calculate_cost_concentration(ingredient_usage_df)
        high_risk_df = identify_high_risk_ingredients(ingredient_usage_df, cost_threshold=20.0, menu_threshold=3)
        high_risk_count = len(high_risk_df) if not high_risk_df.empty else 0
        
        # 점수 계산
        score = 100
        if top3_concentration >= 70:
            score -= 40
        elif top3_concentration >= 50:
            score -= 20
        if high_risk_count > 0:
            score -= 30
        
        status = "안정" if score >= 70 else "주의" if score >= 40 else "위험"
        
        return {
            "status": status,
            "score": max(0, min(100, score)),
            "top3_concentration": top3_concentration,
            "high_risk_count": high_risk_count,
            "message": f"TOP3 집중도 {top3_concentration:.1f}%, 고위험 재료 {high_risk_count}개"
        }
    except Exception as e:
        return {
            "status": "위험",
            "score": 0,
            "top3_concentration": 0.0,
            "high_risk_count": 0,
            "message": f"데이터 로드 실패: {e}"
        }


def _get_revenue_structure_summary(store_id: str, year: int, month: int) -> dict:
    """수익 구조 요약"""
    try:
        fixed_costs = get_fixed_costs(store_id, year, month)
        variable_ratio = get_variable_cost_ratio(store_id, year, month)
        breakeven = calculate_break_even_sales(store_id, year, month)
        monthly_sales = load_monthly_sales_total(store_id, year, month)
        
        # 예상 매출 계산 (간단)
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        if now.year == year and now.month == month:
            days_passed = now.day
            days_in_month = 30  # 간단 추정
            if days_passed > 0:
                estimated_sales = (monthly_sales / days_passed) * days_in_month
            else:
                estimated_sales = monthly_sales
        else:
            estimated_sales = monthly_sales
        
        # 점수 계산
        score = 100
        if breakeven > 0 and estimated_sales > 0:
            ratio = estimated_sales / breakeven
            if ratio < 0.8:  # 손익분기점 대비 80% 미만
                score -= 40
            elif ratio < 1.0:  # 손익분기점 미만
                score -= 20
        
        if variable_ratio > 0.5:  # 변동비율 50% 초과
            score -= 15
        
        status = "안정" if score >= 70 else "주의" if score >= 40 else "위험"
        
        return {
            "status": status,
            "score": max(0, min(100, score)),
            "breakeven": breakeven,
            "variable_ratio": variable_ratio * 100,  # %로 변환
            "estimated_sales": estimated_sales,
            "message": f"손익분기점 {int(breakeven):,}원, 예상 매출 {int(estimated_sales):,}원"
        }
    except Exception as e:
        return {
            "status": "위험",
            "score": 0,
            "breakeven": 0,
            "variable_ratio": 0,
            "estimated_sales": 0,
            "message": f"데이터 로드 실패: {e}"
        }


def get_primary_concern(summary: dict) -> Tuple[str, str, str]:
    """
    가장 의심되는 구조 1개 선택
    
    Returns:
        (concern_name: str, verdict_text: str, target_page: str)
    """
    concerns = []
    
    # 각 구조의 점수와 상태 확인
    if summary["menu_portfolio"]["score"] < 40:
        concerns.append(("메뉴 포트폴리오", summary["menu_portfolio"]["message"], "메뉴 등록"))
    
    if summary["menu_profit"]["score"] < 40:
        concerns.append(("메뉴 수익 구조", summary["menu_profit"]["message"], "메뉴 수익 구조 설계실"))
    
    if summary["ingredient_structure"]["score"] < 40:
        concerns.append(("재료 구조", summary["ingredient_structure"]["message"], "재료 등록"))
    
    if summary["revenue_structure"]["score"] < 40:
        concerns.append(("수익 구조", summary["revenue_structure"]["message"], "수익 구조 설계실"))
    
    # 점수가 가장 낮은 것 우선
    if concerns:
        # 점수 기준으로 정렬
        def get_score_for_concern(concern_name):
            name_map = {
                "메뉴 포트폴리오": "menu_portfolio",
                "메뉴 수익 구조": "menu_profit",
                "재료 구조": "ingredient_structure",
                "수익 구조": "revenue_structure",
            }
            key = name_map.get(concern_name, "menu_portfolio")
            return summary[key]["score"]
        
        concerns.sort(key=lambda x: get_score_for_concern(x[0]))
        
        concern_name, message, target_page = concerns[0]
        verdict_text = f"{concern_name} 구조가 가장 위험합니다. {message}"
        return concern_name, verdict_text, target_page
    
    # 모두 안정적이면 가장 점수가 낮은 것
    all_scores = [
        ("메뉴 포트폴리오", summary["menu_portfolio"]["score"], "메뉴 등록"),
        ("메뉴 수익 구조", summary["menu_profit"]["score"], "메뉴 수익 구조 설계실"),
        ("재료 구조", summary["ingredient_structure"]["score"], "재료 등록"),
        ("수익 구조", summary["revenue_structure"]["score"], "수익 구조 설계실"),
    ]
    all_scores.sort(key=lambda x: x[1])
    
    concern_name, score, target_page = all_scores[0]
    verdict_text = f"{concern_name} 구조를 먼저 점검하세요. (점수: {score}점)"
    
    return concern_name, verdict_text, target_page
