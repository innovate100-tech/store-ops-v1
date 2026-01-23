"""
Impact Engine v1 - 예상효과 ₩ 계산
전략별 월 예상 이익 변화 또는 리스크 회피 금액 계산
"""
from typing import Dict, Optional
from datetime import datetime, date
from zoneinfo import ZoneInfo
from src.storage_supabase import (
    calculate_break_even_sales,
    get_variable_cost_ratio,
    load_monthly_sales_total,
    load_best_available_daily_sales
)


def estimate_impact(strategy_type: str, context: Dict) -> Dict:
    """
    전략별 예상효과 계산
    
    Args:
        strategy_type: "SURVIVAL" | "MARGIN" | "COST" | "PORTFOLIO" | "ACQUISITION" | "OPERATIONS"
        context: {
            "store_id": ...,
            "period": {"year":..., "month":...},
            "kpi": {...},
            "revenue": {...},
            "menu": {...},
            "ingredient": {...},
            "health": {...}
        }
    
    Returns:
        {
            "won": int | None,
            "kind": "profit_up" | "risk_avoid" | "indirect",
            "assumptions": [str, ...],   # 2~4개
            "confidence": float,         # 0.3~0.8
        }
    """
    store_id = context.get("store_id")
    period = context.get("period", {})
    year = period.get("year")
    month = period.get("month")
    
    if not store_id or not year or not month:
        return _get_empty_impact()
    
    kpi = context.get("kpi", {})
    revenue = context.get("revenue", {})
    menu = context.get("menu", {})
    ingredient = context.get("ingredient", {})
    health = context.get("health", {})
    
    # 예상 월 매출 계산
    expected_monthly_sales = _estimate_expected_monthly_sales(store_id, year, month, kpi)
    
    # 변동비율 계산
    variable_cost_rate = revenue.get("variable_cost_rate")
    if variable_cost_rate is None:
        try:
            variable_cost_ratio = get_variable_cost_ratio(store_id, year, month)
            variable_cost_rate = variable_cost_ratio if variable_cost_ratio else 0.3  # 기본 30%
        except Exception:
            variable_cost_rate = 0.3
    
    # 전략별 계산
    if strategy_type == "SURVIVAL":
        return _estimate_survival_impact(store_id, year, month, expected_monthly_sales, variable_cost_rate, revenue)
    elif strategy_type == "MARGIN":
        return _estimate_margin_impact(expected_monthly_sales, health, menu)
    elif strategy_type == "COST":
        return _estimate_cost_impact(expected_monthly_sales, ingredient)
    elif strategy_type == "PORTFOLIO":
        return _estimate_portfolio_impact(expected_monthly_sales, kpi, variable_cost_rate)
    elif strategy_type == "ACQUISITION":
        return _estimate_acquisition_impact(expected_monthly_sales, kpi, variable_cost_rate, health)
    elif strategy_type == "OPERATIONS":
        return _estimate_operations_impact(expected_monthly_sales, variable_cost_rate)
    else:
        return _get_empty_impact()


def _estimate_expected_monthly_sales(store_id: str, year: int, month: int, kpi: Dict) -> float:
    """
    예상 월 매출 계산 (MTD 추세 기반)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        kpi: {
            "mtd_sales": int,  # 월 전체 합계 또는 경과 일수까지의 누적
            "avg_daily_sales": float
        }
    
    Returns:
        float: 예상 월 매출
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # kpi에서 직접 가져오기
    mtd_sales = kpi.get("mtd_sales")
    
    # 디버깅
    if mtd_sales == 0 or mtd_sales is None:
        logger.warning(f"[IMPACT_ENGINE] mtd_sales is {mtd_sales} for store_id={store_id}, year={year}, month={month}")
    
    if mtd_sales and mtd_sales > 0:
        # 경과 일수 계산
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        today = now.date()
        
        # 해당 월의 첫날과 마지막날
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        month_start = date(year, month, 1)
        
        # 경과 일수
        if now.year == year and now.month == month:
            elapsed_days = max(1, (today - month_start).days + 1)
            days_in_month = (next_month - month_start).days
        else:
            # 과거 월이면 실제 일수 사용
            elapsed_days = (next_month - month_start).days
            days_in_month = elapsed_days
        
        if elapsed_days > 0:
            expected = (mtd_sales / elapsed_days) * days_in_month
            return expected
    
    # fallback: kpi의 avg_daily_sales 사용
    avg_daily = kpi.get("avg_daily_sales")
    if avg_daily and avg_daily > 0:
        days_in_month = 30
        return avg_daily * days_in_month
    
    # 최종 fallback: mtd_sales 그대로 (추정 불가)
    return mtd_sales or 0.0


def _estimate_survival_impact(
    store_id: str, year: int, month: int,
    expected_monthly_sales: float,
    variable_cost_rate: float,
    revenue: Dict
) -> Dict:
    """SURVIVAL 전략: 리스크 회피"""
    break_even_sales = revenue.get("break_even_sales")
    if break_even_sales is None:
        try:
            break_even_sales = calculate_break_even_sales(store_id, year, month) or 0
        except Exception:
            break_even_sales = 0
    
    if break_even_sales <= 0 or expected_monthly_sales <= 0:
        return {
            "won": None,
            "kind": "risk_avoid",
            "assumptions": [
                "손익분기점 또는 예상 매출 데이터 부족",
                "추정 불가"
            ],
            "confidence": 0.3
        }
    
    gap = max(0, break_even_sales - expected_monthly_sales)
    if gap <= 0:
        # 이미 손익분기점 넘음
        return {
            "won": 0,
            "kind": "risk_avoid",
            "assumptions": [
                "예상 매출이 손익분기점을 넘음",
                "리스크 회피 효과 없음"
            ],
            "confidence": 0.8
        }
    
    # 리스크 회피 금액 = gap * (1 - variable_cost_rate)
    won = int(gap * (1 - variable_cost_rate))
    
    return {
        "won": won,
        "kind": "risk_avoid",
        "assumptions": [
            f"예상 매출 {expected_monthly_sales:,.0f}원 vs 손익분기점 {break_even_sales:,.0f}원",
            f"부족액 {gap:,.0f}원 × (1 - 변동비율 {variable_cost_rate*100:.0f}%)",
            "변동비 제외 이익 기준"
        ],
        "confidence": 0.7 if expected_monthly_sales > 0 else 0.4
    }


def _estimate_margin_impact(expected_monthly_sales: float, health: Dict, menu: Dict) -> Dict:
    """MARGIN 전략: 공헌이익률 개선"""
    if expected_monthly_sales <= 0:
        return {
            "won": None,
            "kind": "profit_up",
            "assumptions": ["예상 매출 데이터 부족", "추정 불가"],
            "confidence": 0.3
        }
    
    # 건강검진 Q red면 보수적 적용
    health_profile = health if isinstance(health, dict) else {}
    risk_levels = health_profile.get("risk_levels", {})
    q_risk = risk_levels.get("Q", "unknown")
    
    # 공헌이익률 개선 가정
    if q_risk == "red":
        improvement_pct = 0.01  # 1%p 보수
    else:
        improvement_pct = 0.02  # 2%p 기본
    
    won = int(expected_monthly_sales * improvement_pct)
    
    return {
        "won": won,
        "kind": "profit_up",
        "assumptions": [
            f"공헌이익률 +{improvement_pct*100:.1f}%p 개선 가정",
            f"예상 매출 {expected_monthly_sales:,.0f}원 기준",
            "품질(Q) 리스크가 높으면 보수적 적용" if q_risk == "red" else "표준 개선률 적용"
        ],
        "confidence": 0.6
    }


def _estimate_cost_impact(expected_monthly_sales: float, ingredient: Dict) -> Dict:
    """COST 전략: 원가율 개선"""
    if expected_monthly_sales <= 0:
        return {
            "won": None,
            "kind": "profit_up",
            "assumptions": ["예상 매출 데이터 부족", "추정 불가"],
            "confidence": 0.3
        }
    
    # 재료 집중도 확인
    concentration = ingredient.get("top3_cost_concentration_pct", 0) / 100.0 if ingredient.get("top3_cost_concentration_pct") else 0.0
    
    # 원가율 개선 가정
    if concentration > 0.7:
        improvement_pct = 0.02  # 2%p (집중도 높으면 더 개선 가능)
    else:
        improvement_pct = 0.015  # 1.5%p 기본
    
    won = int(expected_monthly_sales * improvement_pct)
    
    return {
        "won": won,
        "kind": "profit_up",
        "assumptions": [
            f"식재료 원가율 -{improvement_pct*100:.1f}%p 개선 가정",
            f"예상 매출 {expected_monthly_sales:,.0f}원 기준",
            f"재료 집중도 {concentration*100:.0f}%" if concentration > 0 else "표준 개선률 적용"
        ],
        "confidence": 0.65
    }


def _estimate_portfolio_impact(expected_monthly_sales: float, kpi: Dict, variable_cost_rate: float) -> Dict:
    """PORTFOLIO 전략: 객단가/전환율 개선"""
    if expected_monthly_sales <= 0:
        return {
            "won": None,
            "kind": "profit_up",
            "assumptions": ["예상 매출 데이터 부족", "추정 불가"],
            "confidence": 0.3
        }
    
    # sales_per_visitor가 있으면 더 정교하게 계산
    sales_per_visitor = kpi.get("sales_per_visitor")
    if sales_per_visitor and sales_per_visitor > 0:
        # 객단가 +3% 가정
        improvement = sales_per_visitor * 0.03
        # 방문자 수 추정 (매출 / 객단가)
        estimated_visitors = expected_monthly_sales / sales_per_visitor
        won = int(improvement * estimated_visitors * (1 - variable_cost_rate))
        
        return {
            "won": won,
            "kind": "profit_up",
            "assumptions": [
                "객단가 +3% 개선 가정",
                f"현재 객단가 {sales_per_visitor:,.0f}원 기준",
                f"추정 방문자 {estimated_visitors:,.0f}명"
            ],
            "confidence": 0.7
        }
    else:
        # fallback: 매출 +2% 가정
        improvement_pct = 0.02
        won = int(expected_monthly_sales * improvement_pct * (1 - variable_cost_rate))
        
        return {
            "won": won,
            "kind": "profit_up",
            "assumptions": [
                "유인 메뉴 도입/정리로 매출 +2% 가정",
                f"예상 매출 {expected_monthly_sales:,.0f}원 기준",
                "객단가 데이터 없음 (보수적 추정)"
            ],
            "confidence": 0.5
        }


def _estimate_acquisition_impact(
    expected_monthly_sales: float,
    kpi: Dict,
    variable_cost_rate: float,
    health: Dict
) -> Dict:
    """ACQUISITION 전략: 방문자 증가"""
    if expected_monthly_sales <= 0:
        return {
            "won": None,
            "kind": "profit_up",
            "assumptions": ["예상 매출 데이터 부족", "추정 불가"],
            "confidence": 0.3
        }
    
    # 건강검진 M red면 보수적 적용
    health_profile = health if isinstance(health, dict) else {}
    risk_levels = health_profile.get("risk_levels", {})
    m_risk = risk_levels.get("M", "unknown")
    
    # 방문자 증가 가정
    if m_risk == "red":
        visitor_increase_pct = 0.03  # 3% 보수
    else:
        visitor_increase_pct = 0.05  # 5% 기본
    
    # visitors 데이터가 있으면 더 정교하게
    visitors_mtd = kpi.get("visitors_mtd")
    if visitors_mtd and visitors_mtd > 0:
        # 경과 일수 계산
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        today = now.date()
        year = now.year
        month = now.month
        
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        month_start = date(year, month, 1)
        
        if now.year == year and now.month == month:
            elapsed_days = max(1, (today - month_start).days + 1)
            days_in_month = (next_month - month_start).days
        else:
            elapsed_days = (next_month - month_start).days
            days_in_month = elapsed_days
        
        if elapsed_days > 0:
            avg_daily_visitors = visitors_mtd / elapsed_days
            expected_monthly_visitors = avg_daily_visitors * days_in_month
            additional_visitors = expected_monthly_visitors * visitor_increase_pct
            
            # 객단가 추정
            sales_per_visitor = kpi.get("sales_per_visitor")
            if not sales_per_visitor or sales_per_visitor <= 0:
                sales_per_visitor = expected_monthly_sales / expected_monthly_visitors if expected_monthly_visitors > 0 else 0
            
            additional_sales = additional_visitors * sales_per_visitor
            won = int(additional_sales * (1 - variable_cost_rate))
            
            return {
                "won": won,
                "kind": "profit_up",
                "assumptions": [
                    f"방문자 +{visitor_increase_pct*100:.0f}% 증가 가정",
                    f"추정 추가 방문자 {additional_visitors:,.0f}명",
                    f"객단가 {sales_per_visitor:,.0f}원 기준"
                ],
                "confidence": 0.7
            }
    
    # fallback: 매출 기반 가정
    won = int(expected_monthly_sales * visitor_increase_pct * (1 - variable_cost_rate))
    
    return {
        "won": won,
        "kind": "profit_up",
        "assumptions": [
            f"방문자 +{visitor_increase_pct*100:.0f}% 증가 가정",
            f"예상 매출 {expected_monthly_sales:,.0f}원 기준",
            "방문자 데이터 없음 (보수적 추정)" if not visitors_mtd else "표준 증가률 적용"
        ],
        "confidence": 0.5
    }


def _estimate_operations_impact(expected_monthly_sales: float, variable_cost_rate: float) -> Dict:
    """OPERATIONS 전략: 리스크 감소 (간접효과)"""
    if expected_monthly_sales <= 0:
        return {
            "won": None,
            "kind": "indirect",
            "assumptions": ["예상 매출 데이터 부족", "추정 불가"],
            "confidence": 0.3
        }
    
    # 운영불안이 매출을 -2% 흔든다고 가정 (보수적)
    risk_reduction_pct = 0.02
    won = int(expected_monthly_sales * risk_reduction_pct * (1 - variable_cost_rate))
    
    return {
        "won": won,
        "kind": "indirect",
        "assumptions": [
            "운영불안 리스크 감소로 매출 안정화",
            "매출 -2% 리스크 회피 가정",
            "간접효과 (정량화 어려움)"
        ],
        "confidence": 0.4
    }


def _get_empty_impact() -> Dict:
    """빈 impact 반환"""
    return {
        "won": None,
        "kind": "indirect",
        "assumptions": ["데이터 부족", "추정 불가"],
        "confidence": 0.3
    }
