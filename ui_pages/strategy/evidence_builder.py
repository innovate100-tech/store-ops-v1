"""
전략 보드 Evidence 생성 모듈
숫자 + 설계 + 검진 3종 근거 표준화
"""

import logging
from typing import Dict, List, Optional
from datetime import date, timedelta
from ui_pages.home.home_data import load_latest_health_diag
from src.health_check.health_integration import get_health_evidence_line

logger = logging.getLogger(__name__)


def build_evidence_bundle(
    store_id: str,
    year: int,
    month: int,
    metrics_bundle: Optional[Dict] = None,
    design_insights: Optional[Dict] = None,
    health_diag: Optional[Dict] = None
) -> List[Dict]:
    """
    Evidence 3종 생성 (숫자/설계/검진)
    
    Returns:
        [
            {"type": "numbers", "title": "...", "summary": "...", "detail": "...", "cta": {...}},
            {"type": "design", "title": "...", "summary": "...", "detail": "...", "cta": {...}},
            {"type": "health", "title": "...", "summary": "...", "detail": "...", "cta": {...}}
        ]
    """
    evidence_list = []
    
    # (A) 숫자 Evidence
    numbers_evidence = _build_numbers_evidence(store_id, year, month, metrics_bundle)
    if numbers_evidence:
        evidence_list.append(numbers_evidence)
    
    # (B) 설계 Evidence
    design_evidence = _build_design_evidence(store_id, year, month, design_insights)
    if design_evidence:
        evidence_list.append(design_evidence)
    
    # (C) 검진 Evidence
    if health_diag is None:
        health_diag = load_latest_health_diag(store_id)
    
    health_evidence = _build_health_evidence(store_id, health_diag)
    if health_evidence:
        evidence_list.append(health_evidence)
    
    # 최대 3개 반환
    return evidence_list[:3]


def _build_numbers_evidence(
    store_id: str,
    year: int,
    month: int,
    metrics_bundle: Optional[Dict] = None
) -> Optional[Dict]:
    """숫자 Evidence 생성"""
    try:
        from src.storage_supabase import (
            load_monthly_sales_total,
            calculate_break_even_sales,
            load_best_available_daily_sales
        )
        
        # 손익분기점 대비 갭
        monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
        break_even = calculate_break_even_sales(store_id, year, month) or 1
        gap_ratio = (monthly_sales / break_even) * 100 if break_even > 0 else 0
        
        if gap_ratio < 95:
            return {
                "type": "numbers",
                "title": "손익분기점 위험",
                "summary": f"손익분기점 대비 {gap_ratio:.0f}% (목표 미달)",
                "detail": f"이번 달 예상 매출이 손익분기점의 {gap_ratio:.0f}% 수준입니다. 즉각적인 수익 구조 개선이 필요합니다.",
                "cta": {
                    "label": "수익 구조 설계실로",
                    "route": "수익 구조 설계실"
                }
            }
        
        # 최근 14일 매출 추세
        today = date.today()
        week_ago = today - timedelta(days=14)
        recent_sales = load_best_available_daily_sales(
            store_id=store_id,
            start_date=week_ago.isoformat(),
            end_date=today.isoformat()
        )
        
        if not recent_sales.empty and len(recent_sales) >= 7:
            if 'total_sales' in recent_sales.columns:
                recent_avg = recent_sales.tail(7)['total_sales'].mean()
                older_avg = recent_sales.head(7)['total_sales'].mean() if len(recent_sales) >= 14 else recent_avg
                
                if recent_avg < older_avg * 0.9:
                    decline_pct = ((older_avg - recent_avg) / older_avg) * 100
                    return {
                        "type": "numbers",
                        "title": "매출 하락 추세",
                        "summary": f"최근 14일 매출 {decline_pct:.0f}% 하락",
                        "detail": f"최근 7일 평균 매출이 이전 7일 대비 {decline_pct:.0f}% 하락했습니다. 원인 분석이 필요합니다.",
                        "cta": {
                            "label": "분석총평",
                            "route": "분석총평"
                        }
                    }
        
        # 기본: 손익분기점 정보
        return {
            "type": "numbers",
            "title": "손익분기점 현황",
            "summary": f"손익분기점 대비 {gap_ratio:.0f}%",
            "detail": f"이번 달 예상 매출이 손익분기점의 {gap_ratio:.0f}% 수준입니다.",
            "cta": {
                "label": "월간 성적표로",
                "route": "월간 성적표"
            }
        }
    
    except Exception as e:
        logger.warning(f"_build_numbers_evidence: Error - {e}")
        return None


def _build_design_evidence(
    store_id: str,
    year: int,
    month: int,
    design_insights: Optional[Dict] = None
) -> Optional[Dict]:
    """설계 Evidence 생성"""
    try:
        if design_insights is None:
            from ui_pages.design_lab.design_insights import get_design_insights
            design_insights = get_design_insights(store_id, year, month)
        
        # 원가 집중도
        ingredient = design_insights.get("ingredient_structure", {})
        top3_concentration = ingredient.get("top3_concentration", 0.0)
        
        if top3_concentration > 0.7:
            return {
                "type": "design",
                "title": "원가 집중 위험",
                "summary": f"재료 TOP3 집중도 {top3_concentration*100:.0f}%",
                "detail": f"재료비의 {top3_concentration*100:.0f}%가 상위 3개 재료에 집중되어 있습니다. 대체재 설계가 필요합니다.",
                "cta": {
                    "label": "재료 구조 설계실로",
                    "route": "재료 등록"
                }
            }
        
        # 고원가율 메뉴
        menu_portfolio = design_insights.get("menu_portfolio", {})
        high_cogs_count = menu_portfolio.get("high_cogs_ratio_menu_count", 0)
        total_menu_count = menu_portfolio.get("total_menu_count", 1)
        
        if high_cogs_count > 0 and total_menu_count > 0:
            high_cogs_ratio = high_cogs_count / total_menu_count
            if high_cogs_ratio > 0.3:
                return {
                    "type": "design",
                    "title": "고원가율 메뉴 과다",
                    "summary": f"원가율 35% 이상 메뉴 {high_cogs_count}개 ({high_cogs_ratio*100:.0f}%)",
                    "detail": f"전체 메뉴 중 {high_cogs_ratio*100:.0f}%가 원가율 35% 이상입니다. 마진 구조 개선이 필요합니다.",
                    "cta": {
                        "label": "메뉴 수익 구조 설계실로",
                        "route": "메뉴 수익 구조 설계실"
                    }
                }
        
        # 포트폴리오 미분류
        unclassified_ratio = menu_portfolio.get("unclassified_ratio", 0.0)
        if unclassified_ratio > 0.3:
            return {
                "type": "design",
                "title": "포트폴리오 미분류",
                "summary": f"역할 태그 미지정 메뉴 {unclassified_ratio*100:.0f}%",
                "detail": f"전체 메뉴 중 {unclassified_ratio*100:.0f}%가 역할 태그가 없습니다. 포트폴리오 재배치가 필요합니다.",
                "cta": {
                    "label": "메뉴 포트폴리오 설계실로",
                    "route": "메뉴 등록"
                }
            }
        
        # 기본: 설계 상태
        return {
            "type": "design",
            "title": "설계 상태",
            "summary": "가게 설계 데이터 확인 필요",
            "detail": "메뉴/재료/레시피 설계 상태를 확인하세요.",
            "cta": {
                "label": "가게 전략 센터로",
                "route": "가게 전략 센터"
            }
        }
    
    except Exception as e:
        logger.warning(f"_build_design_evidence: Error - {e}")
        return None


def _build_health_evidence(
    store_id: str,
    health_diag: Optional[Dict] = None
) -> Optional[Dict]:
    """검진 Evidence 생성"""
    try:
        if health_diag is None:
            health_diag = load_latest_health_diag(store_id)
        
        if not health_diag:
            # 검진 없음: 유도 카드
            return {
                "type": "health",
                "title": "건강검진 미실시",
                "summary": "최근 검진이 없습니다. 이번 주 5분만 투자하세요.",
                "detail": "건강검진을 통해 운영 전반의 위험 신호를 조기에 발견할 수 있습니다.",
                "cta": {
                    "label": "건강검진 실시하기",
                    "route": "건강검진 실시"
                }
            }
        
        # primary_pattern + top risk
        primary_pattern = health_diag.get("primary_pattern", {})
        pattern_title = primary_pattern.get("title", "안정형")
        
        risk_axes = health_diag.get("risk_axes", [])
        top_risk = risk_axes[0] if risk_axes else None
        
        if top_risk:
            risk_axis = top_risk.get("axis", "")
            risk_reason = top_risk.get("reason", "")
            
            return {
                "type": "health",
                "title": f"{pattern_title} 패턴",
                "summary": f"{risk_axis} 축 위험: {risk_reason}",
                "detail": get_health_evidence_line(health_diag) or f"{pattern_title} 패턴이 감지되었습니다.",
                "cta": {
                    "label": "체크결과 보기",
                    "route": "체크결과"
                }
            }
        else:
            return {
                "type": "health",
                "title": f"{pattern_title} 패턴",
                "summary": f"{pattern_title} 상태입니다.",
                "detail": primary_pattern.get("description", ""),
                "cta": {
                    "label": "체크결과 보기",
                    "route": "체크결과"
                }
            }
    
    except Exception as e:
        logger.warning(f"_build_health_evidence: Error - {e}")
        return None
