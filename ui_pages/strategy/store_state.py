"""
가게 상태 분류 엔진 v1
- 가게 상태를 4가지로 분류: survival / recovery / restructure / growth
- 전략 자동 생성의 1단계
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional

from src.storage_supabase import (
    load_best_available_daily_sales,
    load_monthly_sales_total,
    calculate_break_even_sales,
    load_official_daily_sales,
)
from ui_pages.design_lab.design_state_loader import get_design_state


@st.cache_data(ttl=300)
def classify_store_state(store_id: str, year: int, month: int) -> Dict:
    """
    가게 상태 분류
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
    
    Returns:
        {
            "period": {"year": Y, "month": M},
            "state": {"code": "survival|recovery|restructure|growth", "label": "..."},
            "scores": {
                "sales": 0-100,
                "menu": 0-100,
                "ingredient": 0-100,
                "revenue": 0-100,
                "overall": 0-100
            },
            "signals": [
                {"key":"...", "status":"ok|warn|risk", "value":"...", "note":"..."}
            ],
            "primary_reason": "한 줄",
            "evidence": [{"title":"...", "value":"...", "delta":"...", "note":"..."}],
            "debug": {"inputs_used":[...], "notes":[...]}
        }
    """
    if not store_id:
        return _get_empty_state(year, month)
    
    debug = {
        "inputs_used": [],
        "notes": []
    }
    
    try:
        # 1. Revenue Score 계산
        revenue_score, revenue_signals, revenue_evidence = _calculate_revenue_score(
            store_id, year, month, debug
        )
        
        # 2. Sales Score 계산
        sales_score, sales_signals, sales_evidence = _calculate_sales_score(
            store_id, year, month, debug
        )
        
        # 3. Menu Score 계산 (설계 상태 기반)
        menu_score, menu_signals, menu_evidence = _calculate_menu_score(
            store_id, year, month, debug
        )
        
        # 4. Ingredient Score 계산 (설계 상태 기반)
        ingredient_score, ingredient_signals, ingredient_evidence = _calculate_ingredient_score(
            store_id, year, month, debug
        )
        
        # 5. Overall Score 계산
        overall_score = (
            revenue_score * 0.40 +
            sales_score * 0.30 +
            menu_score * 0.15 +
            ingredient_score * 0.15
        )
        
        # 6. 상태 분류
        state_code, state_label, primary_reason = _classify_state(
            revenue_score, sales_score, menu_score, ingredient_score,
            store_id, year, month, debug
        )
        
        # 7. Signals 통합
        all_signals = revenue_signals + sales_signals + menu_signals + ingredient_signals
        
        # 8. Evidence 통합
        all_evidence = revenue_evidence + sales_evidence + menu_evidence + ingredient_evidence
        
        return {
            "period": {"year": year, "month": month},
            "state": {"code": state_code, "label": state_label},
            "scores": {
                "sales": round(sales_score, 1),
                "menu": round(menu_score, 1),
                "ingredient": round(ingredient_score, 1),
                "revenue": round(revenue_score, 1),
                "overall": round(overall_score, 1),
            },
            "signals": all_signals,
            "primary_reason": primary_reason,
            "evidence": all_evidence,
            "debug": debug,
        }
    except Exception as e:
        debug["notes"].append(f"분류 중 오류: {str(e)}")
        return _get_empty_state(year, month, debug)


def _get_empty_state(year: int, month: int, debug: Optional[Dict] = None) -> Dict:
    """빈 상태 반환"""
    if debug is None:
        debug = {"inputs_used": [], "notes": ["데이터 부족"]}
    
    return {
        "period": {"year": year, "month": month},
        "state": {"code": "unknown", "label": "상태 미확인"},
        "scores": {
            "sales": 50.0,
            "menu": 50.0,
            "ingredient": 50.0,
            "revenue": 50.0,
            "overall": 50.0,
        },
        "signals": [{"key": "data_insufficient", "status": "warn", "value": "데이터 부족", "note": ""}],
        "primary_reason": "데이터가 부족하여 상태를 분류할 수 없습니다.",
        "evidence": [],
        "debug": debug,
    }


def _calculate_revenue_score(store_id: str, year: int, month: int, debug: Dict) -> tuple:
    """
    Revenue Score 계산 (0-100)
    
    Returns:
        (score, signals, evidence)
    """
    try:
        debug["inputs_used"].append("revenue_score")
        
        # 손익분기점 계산
        break_even = calculate_break_even_sales(store_id, year, month)
        if break_even <= 0:
            debug["notes"].append("손익분기점 계산 실패")
            return 50.0, [], []
        
        # 예상 매출 계산 (월 누적 / 경과일수 * 월 총일수)
        monthly_sales = load_monthly_sales_total(store_id, year, month)
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        
        if now.year == year and now.month == month:
            days_passed = now.day
            days_in_month = 30  # 간단 추정
            if days_passed > 0:
                expected_sales = (monthly_sales / days_passed) * days_in_month
            else:
                expected_sales = monthly_sales
        else:
            expected_sales = monthly_sales
        
        # 비율 계산
        ratio = (expected_sales / break_even) if break_even > 0 else 0.0
        
        # 점수 계산
        if ratio < 0.95:
            # risk: 20~35
            score = max(20, min(35, 20 + (ratio - 0.8) * 75))  # 0.8~0.95 구간
        elif ratio < 1.05:
            # warn: 40~60
            score = 40 + (ratio - 0.95) * 200  # 0.95~1.05 구간
        else:
            # ok: 70~90
            score = min(90, 70 + (ratio - 1.05) * 200)  # 1.05 이상
        
        # Signals
        signals = []
        if ratio < 0.95:
            signals.append({
                "key": "break_even_gap",
                "status": "risk",
                "value": f"{ratio*100:.0f}%",
                "note": "예상매출이 손익분기점보다 낮습니다"
            })
        elif ratio < 1.05:
            signals.append({
                "key": "break_even_near",
                "status": "warn",
                "value": f"{ratio*100:.0f}%",
                "note": "손익분기점 근접"
            })
        else:
            signals.append({
                "key": "break_even_safe",
                "status": "ok",
                "value": f"{ratio*100:.0f}%",
                "note": "손익분기점 여유"
            })
        
        # Evidence
        evidence = [
            {
                "title": "손익분기점",
                "value": f"{break_even:,.0f}원",
                "delta": None,
                "note": ""
            },
            {
                "title": "예상 매출",
                "value": f"{expected_sales:,.0f}원",
                "delta": None,
                "note": f"대비 {ratio*100:.0f}%"
            }
        ]
        
        return score, signals, evidence
    except Exception as e:
        debug["notes"].append(f"Revenue score 계산 오류: {str(e)}")
        return 50.0, [], []


def _calculate_sales_score(store_id: str, year: int, month: int, debug: Dict) -> tuple:
    """
    Sales Score 계산 (0-100)
    최근 14일 전주 대비 하락 신호 사용
    """
    try:
        debug["inputs_used"].append("sales_score")
        
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        
        # 최근 14일
        recent_end = today
        recent_start = today - timedelta(days=13)
        
        # 전주 14일
        compare_end = recent_start - timedelta(days=1)
        compare_start = compare_end - timedelta(days=13)
        
        # 데이터 로드
        start_date = (compare_start - timedelta(days=2)).isoformat()
        end_date = recent_end.isoformat()
        
        sales_df = load_best_available_daily_sales(
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if sales_df.empty:
            debug["notes"].append("매출 데이터 없음")
            return 50.0, [], []
        
        # 날짜 변환
        sales_df['date'] = sales_df['date'].apply(
            lambda x: x.date() if isinstance(x, datetime) else x
        )
        
        # 최근 구간
        recent_df = sales_df[
            (sales_df['date'] >= recent_start) &
            (sales_df['date'] <= recent_end)
        ]
        
        # 비교 구간
        compare_df = sales_df[
            (sales_df['date'] >= compare_start) &
            (sales_df['date'] <= compare_end)
        ]
        
        if recent_df.empty or compare_df.empty:
            debug["notes"].append("비교 구간 데이터 부족")
            return 50.0, [], []
        
        # 평균 매출 계산
        recent_avg = recent_df['total_sales'].mean() if 'total_sales' in recent_df.columns else 0
        compare_avg = compare_df['total_sales'].mean() if 'total_sales' in compare_df.columns else 0
        
        if compare_avg <= 0:
            debug["notes"].append("비교 구간 매출 0")
            return 50.0, [], []
        
        # 변화율
        change_pct = ((recent_avg - compare_avg) / compare_avg * 100)
        
        # 점수 계산
        if change_pct < -15:
            # 하락 강함: 20~40
            score = max(20, min(40, 40 + (change_pct + 15) * 1.33))
        elif change_pct < -5:
            # 하락 보통: 40~60
            score = 40 + (change_pct + 15) * 2
        elif change_pct < 5:
            # 안정: 60~80
            score = 60 + change_pct * 2
        else:
            # 상승: 80~90
            score = min(90, 80 + (change_pct - 5) * 0.5)
        
        # Signals
        signals = []
        if change_pct < -15:
            signals.append({
                "key": "sales_drop_severe",
                "status": "risk",
                "value": f"{change_pct:.1f}%",
                "note": "매출 급락"
            })
        elif change_pct < -5:
            signals.append({
                "key": "sales_drop_moderate",
                "status": "warn",
                "value": f"{change_pct:.1f}%",
                "note": "매출 하락"
            })
        elif change_pct >= 5:
            signals.append({
                "key": "sales_growth",
                "status": "ok",
                "value": f"+{change_pct:.1f}%",
                "note": "매출 상승"
            })
        else:
            signals.append({
                "key": "sales_stable",
                "status": "ok",
                "value": f"{change_pct:.1f}%",
                "note": "매출 안정"
            })
        
        # Evidence
        evidence = [
            {
                "title": "최근 14일 평균",
                "value": f"{recent_avg:,.0f}원",
                "delta": f"{change_pct:+.1f}%",
                "note": "전주 대비"
            }
        ]
        
        return score, signals, evidence
    except Exception as e:
        debug["notes"].append(f"Sales score 계산 오류: {str(e)}")
        return 50.0, [], []


def _calculate_menu_score(store_id: str, year: int, month: int, debug: Dict) -> tuple:
    """
    Menu Score 계산 (0-100)
    설계 상태 기반
    """
    try:
        debug["inputs_used"].append("menu_score")
        
        design_state = get_design_state(store_id, year, month)
        menu_portfolio_state = design_state.get("menu_portfolio", {})
        menu_profit_state = design_state.get("menu_profit", {})
        
        # 포트폴리오 점수와 수익 점수 평균
        portfolio_score = menu_portfolio_state.get("score", 50)
        profit_score = menu_profit_state.get("score", 50)
        menu_score = (portfolio_score + profit_score) / 2
        
        # Signals
        signals = []
        portfolio_signals = menu_portfolio_state.get("signals", [])
        profit_signals = menu_profit_state.get("signals", [])
        
        for sig in portfolio_signals[:2]:  # 최대 2개
            signals.append({
                "key": f"menu_portfolio_{sig}",
                "status": menu_portfolio_state.get("status", "safe"),
                "value": sig,
                "note": ""
            })
        
        for sig in profit_signals[:2]:  # 최대 2개
            signals.append({
                "key": f"menu_profit_{sig}",
                "status": menu_profit_state.get("status", "safe"),
                "value": sig,
                "note": ""
            })
        
        # Evidence
        evidence = [
            {
                "title": "메뉴 포트폴리오 점수",
                "value": f"{portfolio_score:.0f}점",
                "delta": None,
                "note": menu_portfolio_state.get("status", "safe")
            },
            {
                "title": "메뉴 수익 구조 점수",
                "value": f"{profit_score:.0f}점",
                "delta": None,
                "note": menu_profit_state.get("status", "safe")
            }
        ]
        
        return menu_score, signals, evidence
    except Exception as e:
        debug["notes"].append(f"Menu score 계산 오류: {str(e)}")
        return 50.0, [], []


def _calculate_ingredient_score(store_id: str, year: int, month: int, debug: Dict) -> tuple:
    """
    Ingredient Score 계산 (0-100)
    설계 상태 기반
    """
    try:
        debug["inputs_used"].append("ingredient_score")
        
        design_state = get_design_state(store_id, year, month)
        ingredient_state = design_state.get("ingredient_structure", {})
        
        ingredient_score = ingredient_state.get("score", 50)
        
        # Signals
        signals = []
        ingredient_signals = ingredient_state.get("signals", [])
        for sig in ingredient_signals[:3]:  # 최대 3개
            signals.append({
                "key": f"ingredient_{sig}",
                "status": ingredient_state.get("status", "safe"),
                "value": sig,
                "note": ""
            })
        
        # Evidence
        evidence = [
            {
                "title": "재료 구조 점수",
                "value": f"{ingredient_score:.0f}점",
                "delta": None,
                "note": ingredient_state.get("status", "safe")
            }
        ]
        
        return ingredient_score, signals, evidence
    except Exception as e:
        debug["notes"].append(f"Ingredient score 계산 오류: {str(e)}")
        return 50.0, [], []


def _classify_state(
    revenue_score: float,
    sales_score: float,
    menu_score: float,
    ingredient_score: float,
    store_id: str,
    year: int,
    month: int,
    debug: Dict
) -> tuple:
    """
    상태 분류
    
    Returns:
        (state_code, state_label, primary_reason)
    """
    try:
        # 손익분기점 정보 재확인 (survival 판단용)
        break_even = calculate_break_even_sales(store_id, year, month)
        monthly_sales = load_monthly_sales_total(store_id, year, month)
        
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        
        if now.year == year and now.month == month:
            days_passed = now.day
            days_in_month = 30
            if days_passed > 0:
                expected_sales = (monthly_sales / days_passed) * days_in_month
            else:
                expected_sales = monthly_sales
        else:
            expected_sales = monthly_sales
        
        ratio = (expected_sales / break_even) if break_even > 0 else 1.0
        
        # 1. Survival
        if (break_even > 0 and expected_sales > 0 and expected_sales < break_even) or revenue_score <= 35:
            return (
                "survival",
                "생존선 복구",
                f"예상 매출({expected_sales:,.0f}원)이 손익분기점({break_even:,.0f}원)보다 낮습니다."
            )
        
        # 2. Recovery
        if sales_score <= 45:
            return (
                "recovery",
                "회복 모드",
                f"매출이 하락 중입니다(점수 {sales_score:.0f}점). 회복이 필요합니다."
            )
        
        # 3. Restructure
        if (menu_score < 40 or ingredient_score < 40) and sales_score >= 50:
            if menu_score < 40:
                return (
                    "restructure",
                    "구조 개편",
                    f"메뉴 구조 점수가 낮습니다({menu_score:.0f}점). 구조 개편이 필요합니다."
                )
            else:
                return (
                    "restructure",
                    "구조 개편",
                    f"재료 구조 점수가 낮습니다({ingredient_score:.0f}점). 구조 개편이 필요합니다."
                )
        
        # 4. Growth
        return (
            "growth",
            "성장 최적화",
            "전반적으로 안정적인 상태입니다. 성장 최적화에 집중할 수 있습니다."
        )
    except Exception as e:
        debug["notes"].append(f"상태 분류 오류: {str(e)}")
        return "unknown", "상태 미확인", "상태 분류 중 오류가 발생했습니다."
