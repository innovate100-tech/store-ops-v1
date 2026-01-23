"""
기존 판결 로직을 CoachVerdict로 변환하는 어댑터
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from ui_pages.coach.coach_contract import CoachVerdict, Evidence, Action
from ui_pages.design_lab.design_center_data import get_design_center_summary, get_primary_concern


def get_home_coach_verdict(store_id: str, year: int, month: int) -> CoachVerdict:
    """HOME v2 판결을 CoachVerdict로 변환"""
    # 순환 import 방지를 위해 함수 내부에서 import
    from ui_pages.home.home_verdict import get_coach_verdict
    from src.storage_supabase import load_monthly_sales_total
    
    monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
    verdict_dict = get_coach_verdict(store_id, year, month, monthly_sales)
    
    # Level 결정
    if verdict_dict.get("verdict_type") is None:
        level = "OK"
    elif verdict_dict.get("verdict_type") in ["revenue_structure", "menu_profit", "ingredient_structure"]:
        level = "RISK"
    else:
        level = "WARN"
    
    # Evidence 변환
    evidence_list = []
    for reason in verdict_dict.get("reasons", [])[:4]:
        evidence_list.append(Evidence(
            label=reason.get("title", ""),
            value=reason.get("value", ""),
            note=None
        ))
    
    # Actions 변환
    actions_list = []
    if verdict_dict.get("target_page"):
        actions_list.append(Action(
            label=verdict_dict.get("button_label", "확인하기"),
            page=verdict_dict.get("target_page", "홈"),
            intent=verdict_dict.get("verdict_type")
        ))
    
    # Title과 Summary
    title = verdict_dict.get("verdict_text", "판결 없음")
    summary = verdict_dict.get("verdict_text", "")
    
    # 날짜
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    as_of = now.strftime("%Y-%m-%d")
    
    return CoachVerdict(
        level=level,
        title=title,
        summary=summary,
        evidence=evidence_list if evidence_list else [Evidence(label="데이터", value="분석 중", note=None)],
        actions=actions_list if actions_list else [Action(label="홈으로", page="홈", intent=None)],
        source="home",
        as_of=as_of
    )


def get_design_center_verdict(store_id: str) -> CoachVerdict:
    """Design Center 판결을 CoachVerdict로 변환"""
    summary = get_design_center_summary(store_id)
    concern_name, verdict_text, target_page = get_primary_concern(summary)
    
    # Level 결정 (점수 기반)
    min_score = min(
        summary["menu_portfolio"]["score"],
        summary["menu_profit"]["score"],
        summary["ingredient_structure"]["score"],
        summary["revenue_structure"]["score"]
    )
    
    if min_score < 40:
        level = "RISK"
    elif min_score < 70:
        level = "WARN"
    else:
        level = "OK"
    
    # Evidence 변환
    evidence_list = [
        Evidence(
            label="메뉴 포트폴리오",
            value=f"{summary['menu_portfolio']['score']}점 ({summary['menu_portfolio']['status']})",
            note=summary['menu_portfolio']['message']
        ),
        Evidence(
            label="메뉴 수익 구조",
            value=f"{summary['menu_profit']['score']}점 ({summary['menu_profit']['status']})",
            note=summary['menu_profit']['message']
        ),
        Evidence(
            label="재료 구조",
            value=f"{summary['ingredient_structure']['score']}점 ({summary['ingredient_structure']['status']})",
            note=summary['ingredient_structure']['message']
        ),
        Evidence(
            label="수익 구조",
            value=f"{summary['revenue_structure']['score']}점 ({summary['revenue_structure']['status']})",
            note=summary['revenue_structure']['message']
        ),
    ]
    
    # Actions 변환
    actions_list = [
        Action(
            label=f"{concern_name} 점검하기",
            page=target_page,
            intent=concern_name
        )
    ]
    
    # 날짜
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    as_of = now.strftime("%Y-%m-%d")
    
    return CoachVerdict(
        level=level,
        title=f"{concern_name} 구조가 가장 의심됩니다",
        summary=verdict_text,
        evidence=evidence_list,
        actions=actions_list,
        source="design_center",
        as_of=as_of
    )
