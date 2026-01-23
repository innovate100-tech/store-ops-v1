"""
월간 구조 리포트
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional
from ui_pages.design_lab.design_center_data import get_design_center_summary, get_primary_concern
from ui_pages.coach.coach_adapters import get_design_center_verdict
from ui_pages.coach.coach_contract import CoachVerdict


def build_monthly_structure_report(store_id: str, year: int, month: int) -> dict:
    """
    월간 구조 리포트 생성
    
    Returns:
        {
            "verdicts": List[CoachVerdict],  # 4개 구조 판결 요약
            "primary_concern": CoachVerdict,  # 이번 달 최우선 구조
            "delta_vs_prev_month": dict,  # 지난달 대비 변화 (가능한 범위만)
            "next_month_actions": List[dict]  # 다음달 추천 과제
        }
    """
    # 현재 달 요약
    summary = get_design_center_summary(store_id)
    primary_verdict = get_design_center_verdict(store_id)
    
    # 4개 구조 판결 요약 (간단 버전)
    verdicts = []
    for key, data in [
        ("menu_portfolio", summary["menu_portfolio"]),
        ("menu_profit", summary["menu_profit"]),
        ("ingredient_structure", summary["ingredient_structure"]),
        ("revenue_structure", summary["revenue_structure"]),
    ]:
        from ui_pages.coach.coach_contract import Evidence, Action
        
        level = "OK" if data["score"] >= 70 else "WARN" if data["score"] >= 40 else "RISK"
        
        verdicts.append(CoachVerdict(
            level=level,
            title=f"{_get_structure_name(key)} 구조",
            summary=data["message"],
            evidence=[
                Evidence(label="점수", value=f"{data['score']}점", note=data["status"]),
                Evidence(label="상태", value=data["status"], note=None),
            ],
            actions=[
                Action(label=f"{_get_structure_name(key)} 점검", page=_get_structure_page(key), intent=key)
            ],
            source="monthly_report",
            as_of=datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
        ))
    
    # 지난달 대비 변화 (간단 버전 - 가능한 범위만)
    delta_vs_prev_month = {}
    try:
        # 이전 달 계산
        prev_month = month - 1
        prev_year = year
        if prev_month <= 0:
            prev_month = 12
            prev_year = year - 1
        
        # 이전 달 요약 (에러 처리)
        try:
            prev_summary = get_design_center_summary(store_id)  # 현재는 같은 로직 사용 (실제로는 이전 달 데이터 필요)
            delta_vs_prev_month = {
                "menu_portfolio": {
                    "score_change": summary["menu_portfolio"]["score"] - prev_summary["menu_portfolio"]["score"],
                    "status_change": summary["menu_portfolio"]["status"] != prev_summary["menu_portfolio"]["status"]
                },
                "menu_profit": {
                    "score_change": summary["menu_profit"]["score"] - prev_summary["menu_profit"]["score"],
                    "status_change": summary["menu_profit"]["status"] != prev_summary["menu_profit"]["status"]
                },
                "ingredient_structure": {
                    "score_change": summary["ingredient_structure"]["score"] - prev_summary["ingredient_structure"]["score"],
                    "status_change": summary["ingredient_structure"]["status"] != prev_summary["ingredient_structure"]["status"]
                },
                "revenue_structure": {
                    "score_change": summary["revenue_structure"]["score"] - prev_summary["revenue_structure"]["score"],
                    "status_change": summary["revenue_structure"]["status"] != prev_summary["revenue_structure"]["status"]
                },
            }
        except Exception:
            delta_vs_prev_month = {"message": "지난달 데이터 부족"}
    except Exception:
        delta_vs_prev_month = {"message": "지난달 비교 불가"}
    
    # 다음달 추천 과제
    next_month_actions = []
    for key, data in [
        ("menu_portfolio", summary["menu_portfolio"]),
        ("menu_profit", summary["menu_profit"]),
        ("ingredient_structure", summary["ingredient_structure"]),
        ("revenue_structure", summary["revenue_structure"]),
    ]:
        if data["score"] < 70:
            next_month_actions.append({
                "label": f"{_get_structure_name(key)} 개선하기",
                "page": _get_structure_page(key),
                "reason": data["message"]
            })
    
    # 최대 3개만
    next_month_actions = next_month_actions[:3]
    
    return {
        "verdicts": verdicts,
        "primary_concern": primary_verdict,
        "delta_vs_prev_month": delta_vs_prev_month,
        "next_month_actions": next_month_actions
    }


def _get_structure_name(key: str) -> str:
    """구조명 반환"""
    names = {
        "menu_portfolio": "메뉴 포트폴리오",
        "menu_profit": "메뉴 수익 구조",
        "ingredient_structure": "재료 구조",
        "revenue_structure": "수익 구조",
    }
    return names.get(key, key)


def _get_structure_page(key: str) -> str:
    """구조별 페이지 반환"""
    pages = {
        "menu_portfolio": "메뉴 등록",
        "menu_profit": "메뉴 수익 구조 설계실",
        "ingredient_structure": "재료 등록",
        "revenue_structure": "수익 구조 설계실",
    }
    return pages.get(key, "홈")
