"""
설계 상태 통합 로더
- 각 설계실 DB/세션 데이터를 읽어서 통합 구조 상태를 반환
- 점수화(0-100) 및 상태 판정(safe/warn/risk) 포함
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List

from ui_pages.design_lab.design_insights import get_design_insights
from src.storage_supabase import (
    load_csv,
    load_menu_role_tags,
    load_ingredient_structure_state,
    load_monthly_sales_total,
    calculate_break_even_sales,
)


@st.cache_data(ttl=300)
def get_design_state(store_id: str, year: int = None, month: int = None) -> Dict:
    """
    설계 상태 통합 로드
    
    Args:
        store_id: 매장 ID
        year: 연도 (없으면 현재)
        month: 월 (없으면 현재)
    
    Returns:
        {
            "menu_portfolio": {
                "score": int,  # 0-100
                "status": "safe" | "warn" | "risk",
                "signals": List[str],
                "raw": {...}
            },
            "menu_profit": {...},
            "ingredient_structure": {...},
            "revenue_structure": {...}
        }
    """
    if not store_id:
        return _get_empty_state()
    
    try:
        # 현재 날짜 기본값
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        # 기존 insights 로드
        insights = get_design_insights(store_id, year, month)
        
        # 각 영역별 상태 계산
        return {
            "menu_portfolio": _calculate_menu_portfolio_state(insights.get("menu_portfolio", {})),
            "menu_profit": _calculate_menu_profit_state(insights.get("menu_profit", {})),
            "ingredient_structure": _calculate_ingredient_structure_state(insights.get("ingredient_structure", {})),
            "revenue_structure": _calculate_revenue_structure_state(insights.get("revenue_structure", {})),
        }
    except Exception as e:
        return _get_empty_state()


def _get_empty_state() -> Dict:
    """빈 상태 구조 반환"""
    empty_area = {
        "score": 0,
        "status": "risk",
        "signals": ["데이터 부족"],
        "raw": {},
    }
    return {
        "menu_portfolio": empty_area.copy(),
        "menu_profit": empty_area.copy(),
        "ingredient_structure": empty_area.copy(),
        "revenue_structure": empty_area.copy(),
    }


def _calculate_menu_portfolio_state(insights: Dict) -> Dict:
    """메뉴 포트폴리오 상태 계산"""
    if not insights.get("has_data", False):
        return {
            "score": 0,
            "status": "risk",
            "signals": ["메뉴 데이터 없음"],
            "raw": insights,
        }
    
    signals = []
    score = 100
    status = "safe"
    
    # 마진 메뉴 0개
    margin_count = insights.get("margin_menu_count", 0)
    if margin_count == 0:
        signals.append("마진 메뉴 0개")
        score -= 40
        status = "risk"
    
    # 미분류 비율
    unclassified_ratio = insights.get("role_unclassified_ratio", 0.0)
    if unclassified_ratio >= 30.0:
        signals.append(f"미분류 메뉴 {unclassified_ratio:.0f}%")
        score -= 30
        if status == "safe":
            status = "warn"
    elif unclassified_ratio >= 20.0:
        signals.append(f"미분류 메뉴 {unclassified_ratio:.0f}%")
        score -= 15
        if status == "safe":
            status = "warn"
    
    # 유인 메뉴 과다
    bait_ratio = insights.get("bait_ratio", 0.0)
    if bait_ratio >= 50.0:
        signals.append(f"유인 메뉴 과다 ({bait_ratio:.0f}%)")
        score -= 20
        if status == "safe":
            status = "warn"
    
    # 포트폴리오 균형 점수
    balance_score = insights.get("portfolio_balance_score", 0)
    if balance_score < 40:
        signals.append("포트폴리오 균형 불량")
        score -= 20
        if status == "safe":
            status = "warn"
    elif balance_score < 60:
        signals.append("포트폴리오 균형 개선 필요")
        score -= 10
    
    # 점수 보정 (0-100 범위)
    score = max(0, min(100, score))
    
    # 상태 재판정
    if score < 40:
        status = "risk"
    elif score < 70:
        status = "warn"
    else:
        status = "safe"
    
    # 신호가 없으면 안전 신호
    if not signals:
        signals.append("포트폴리오 구조 양호")
    
    return {
        "score": score,
        "status": status,
        "signals": signals,
        "raw": insights,
    }


def _calculate_menu_profit_state(insights: Dict) -> Dict:
    """메뉴 수익 구조 상태 계산"""
    if not insights.get("has_data", False):
        return {
            "score": 0,
            "status": "risk",
            "signals": ["메뉴 원가 데이터 없음"],
            "raw": insights,
        }
    
    signals = []
    score = 100
    status = "safe"
    
    # 최악 원가율
    worst_cogs = insights.get("worst_cogs_ratio", 0.0)
    if worst_cogs >= 50.0:
        signals.append(f"최악 원가율 {worst_cogs:.0f}%")
        score -= 40
        status = "risk"
    elif worst_cogs >= 40.0:
        signals.append(f"고원가율 메뉴 존재 ({worst_cogs:.0f}%)")
        score -= 25
        if status == "safe":
            status = "warn"
    
    # 고원가율 메뉴 개수
    high_cogs_count = insights.get("high_cogs_ratio_menu_count", 0)
    if high_cogs_count >= 3:
        signals.append(f"고원가율 메뉴 {high_cogs_count}개")
        score -= 30
        if status == "safe":
            status = "warn"
    elif high_cogs_count >= 1:
        signals.append(f"고원가율 메뉴 {high_cogs_count}개")
        score -= 15
    
    # 저공헌이익 메뉴
    low_contribution_count = insights.get("low_contribution_menu_count", 0)
    if low_contribution_count >= 3:
        signals.append(f"저공헌이익 메뉴 {low_contribution_count}개")
        score -= 25
        if status == "safe":
            status = "warn"
    elif low_contribution_count >= 1:
        signals.append(f"저공헌이익 메뉴 {low_contribution_count}개")
        score -= 10
    
    # 점수 보정
    score = max(0, min(100, score))
    
    # 상태 재판정
    if score < 40:
        status = "risk"
    elif score < 70:
        status = "warn"
    else:
        status = "safe"
    
    if not signals:
        signals.append("메뉴 수익 구조 양호")
    
    return {
        "score": score,
        "status": status,
        "signals": signals,
        "raw": insights,
    }


def _calculate_ingredient_structure_state(insights: Dict) -> Dict:
    """재료 구조 상태 계산"""
    if not insights.get("has_data", False):
        return {
            "score": 0,
            "status": "risk",
            "signals": ["재료 데이터 없음"],
            "raw": insights,
        }
    
    signals = []
    score = 100
    status = "safe"
    
    # TOP3 집중도
    concentration = insights.get("top3_concentration", 0.0)
    if concentration >= 0.70:
        signals.append(f"TOP3 재료 집중도 {concentration*100:.0f}%")
        score -= 40
        status = "risk"
    elif concentration >= 0.60:
        signals.append(f"TOP3 재료 집중도 {concentration*100:.0f}%")
        score -= 25
        if status == "safe":
            status = "warn"
    
    # 고위험 재료
    high_risk_count = insights.get("high_risk_ingredient_count", 0)
    if high_risk_count >= 3:
        signals.append(f"고위험 재료 {high_risk_count}개")
        score -= 30
        if status == "safe":
            status = "warn"
    elif high_risk_count >= 1:
        signals.append(f"고위험 재료 {high_risk_count}개")
        score -= 15
    
    # 대체재 미설정
    missing_substitute = insights.get("missing_substitute_count", 0)
    if missing_substitute >= 3:
        signals.append(f"대체재 미설정 {missing_substitute}개")
        score -= 20
        if status == "safe":
            status = "warn"
    
    # 발주유형 미설정
    missing_order_type = insights.get("missing_order_type_count", 0)
    if missing_order_type >= 3:
        signals.append(f"발주유형 미설정 {missing_order_type}개")
        score -= 15
        if status == "safe":
            status = "warn"
    
    # 점수 보정
    score = max(0, min(100, score))
    
    # 상태 재판정
    if score < 40:
        status = "risk"
    elif score < 70:
        status = "warn"
    else:
        status = "safe"
    
    if not signals:
        signals.append("재료 구조 양호")
    
    return {
        "score": score,
        "status": status,
        "signals": signals,
        "raw": insights,
    }


def _calculate_revenue_structure_state(insights: Dict) -> Dict:
    """수익 구조 상태 계산"""
    if not insights.get("has_data", False):
        return {
            "score": 0,
            "status": "risk",
            "signals": ["수익 구조 데이터 없음"],
            "raw": insights,
        }
    
    signals = []
    score = 100
    status = "safe"
    
    # 손익분기점 대비 비율
    gap_ratio = insights.get("break_even_gap_ratio", 0.0)
    if gap_ratio < 0.8:
        signals.append(f"손익분기점 대비 {gap_ratio*100:.0f}%")
        score -= 50
        status = "risk"
    elif gap_ratio < 1.0:
        signals.append(f"손익분기점 근접 ({gap_ratio*100:.0f}%)")
        score -= 30
        if status == "safe":
            status = "warn"
    elif gap_ratio < 1.2:
        signals.append(f"손익분기점 여유 적음 ({gap_ratio*100:.0f}%)")
        score -= 10
    
    # 점수 보정
    score = max(0, min(100, score))
    
    # 상태 재판정
    if score < 40:
        status = "risk"
    elif score < 70:
        status = "warn"
    else:
        status = "safe"
    
    if not signals:
        signals.append("수익 구조 양호")
    
    return {
        "score": score,
        "status": status,
        "signals": signals,
        "raw": insights,
    }


def get_primary_risk_area(design_state: Dict) -> str:
    """
    가장 위험한 설계 영역 반환
    
    Returns:
        "menu_portfolio" | "menu_profit" | "ingredient_structure" | "revenue_structure" | None
    """
    if not design_state:
        return None
    
    risk_areas = []
    for area_name, area_state in design_state.items():
        if area_state.get("status") == "risk":
            risk_areas.append((area_name, area_state.get("score", 100)))
    
    if not risk_areas:
        # risk가 없으면 warn 중에서 최저 점수
        warn_areas = []
        for area_name, area_state in design_state.items():
            if area_state.get("status") == "warn":
                warn_areas.append((area_name, area_state.get("score", 100)))
        
        if warn_areas:
            warn_areas.sort(key=lambda x: x[1])  # 점수 낮은 순
            return warn_areas[0][0]
        
        return None
    
    # risk 중에서 점수 낮은 순
    risk_areas.sort(key=lambda x: x[1])
    return risk_areas[0][0]
