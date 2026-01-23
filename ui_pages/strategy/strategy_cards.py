"""
전략 카드 TOP3 생성 엔진 v1
- 10-7A의 가게 상태 분류 결과 + 설계/매출 신호를 이용해서 전략 카드 3장 생성
- v4: 건강검진 통합 + Impact/Action Plan 추가
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional

from ui_pages.strategy.store_state import classify_store_state
from ui_pages.design_lab.design_state_loader import get_design_state
from ui_pages.design_lab.design_insights import get_design_insights


@st.cache_data(ttl=300)
def build_strategy_cards(
    store_id: str,
    year: int,
    month: int,
    state_payload: Optional[Dict] = None,
    use_v4: bool = True  # v4 엔진 사용 여부 (건강검진 통합)
) -> Dict:
    """
    전략 카드 TOP3 생성
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        state_payload: 가게 상태 분류 결과 (없으면 자동 호출)
    
    Returns:
        {
            "period": {"year": Y, "month": M},
            "store_state": {...},
            "cards": [
                {
                    "rank": 1,
                    "title": "...",
                    "goal": "...",
                    "why": "...",
                    "evidence": [...],
                    "cta": {"label": "...", "page": "...", "params": {}}
                },
                ...
            ],
            "debug": {"rules_fired": [...], "notes": [...]}
        }
    """
    if not store_id:
        return _get_empty_cards(year, month)
    
    debug = {
        "rules_fired": [],
        "notes": []
    }
    
    try:
        # v4 엔진 사용 시 (건강검진 통합)
        if use_v4:
            return _build_strategy_cards_v4(store_id, year, month, state_payload, debug)
        
        # 기존 v1 엔진 (하위 호환)
        # 1. 가게 상태 분류 (없으면 호출)
        if state_payload is None:
            state_payload = classify_store_state(store_id, year, month)
        
        store_state = state_payload.get("state", {})
        scores = state_payload.get("scores", {})
        state_code = store_state.get("code", "unknown")
        
        # 2. 설계 인사이트 로드
        design_insights = get_design_insights(store_id, year, month)
        design_state = get_design_state(store_id, year, month)
        
        # 3. 카드 후보 생성
        candidate_cards = []
        
        # 카드 1: 생존선 복구 (Revenue)
        if _should_show_survival_card(scores, state_payload, debug):
            card = _build_survival_card(store_id, year, month, state_payload, design_insights)
            if card:
                candidate_cards.append(("survival", card))
                debug["rules_fired"].append("생존선 복구 카드")
        
        # 카드 2: 마진 구조 복구 (Menu Profit)
        if _should_show_menu_profit_card(design_insights, design_state, debug):
            card = _build_menu_profit_card(store_id, design_insights, design_state)
            if card:
                candidate_cards.append(("menu_profit", card))
                debug["rules_fired"].append("마진 구조 복구 카드")
        
        # 카드 3: 원가 집중 분산 (Ingredient)
        if _should_show_ingredient_card(design_insights, design_state, debug):
            card = _build_ingredient_card(store_id, design_insights, design_state)
            if card:
                candidate_cards.append(("ingredient", card))
                debug["rules_fired"].append("원가 집중 분산 카드")
        
        # 카드 4: 포트폴리오 재배치 (Portfolio)
        if _should_show_portfolio_card(design_insights, design_state, debug):
            card = _build_portfolio_card(store_id, design_insights, design_state)
            if card:
                candidate_cards.append(("portfolio", card))
                debug["rules_fired"].append("포트폴리오 재배치 카드")
        
        # 카드 5: 매출 하락 원인 찾기 (Sales Recovery)
        if _should_show_sales_recovery_card(scores, state_payload, debug):
            card = _build_sales_recovery_card(store_id, scores, state_payload)
            if card:
                candidate_cards.append(("sales_recovery", card))
                debug["rules_fired"].append("매출 하락 원인 찾기 카드")
        
        # 4. 우선순위 정렬 및 중복 제거
        selected_cards = _select_top3_cards(candidate_cards, debug)
        
        # 5. 3장 미만이면 Fallback으로 채움
        while len(selected_cards) < 3:
            fallback_card = _build_fallback_card(store_id)
            selected_cards.append(fallback_card)
            debug["rules_fired"].append("Fallback 카드")
        
        # 6. rank 부여
        for idx, card in enumerate(selected_cards[:3], 1):
            card["rank"] = idx
        
        return {
            "period": {"year": year, "month": month},
            "store_state": {
                "code": state_code,
                "label": store_state.get("label", ""),
                "scores": scores,
            },
            "cards": selected_cards[:3],
            "debug": debug,
        }
    except Exception as e:
        debug["notes"].append(f"카드 생성 오류: {str(e)}")
        return _get_empty_cards(year, month, debug)


def _get_empty_cards(year: int, month: int, debug: Optional[Dict] = None) -> Dict:
    """빈 카드 반환"""
    if debug is None:
        debug = {"rules_fired": [], "notes": ["데이터 부족"]}
    
    fallback_card = _build_fallback_card(None)
    fallback_card["rank"] = 1
    
    return {
        "period": {"year": year, "month": month},
        "store_state": {"code": "unknown", "label": "상태 미확인", "scores": {}},
        "cards": [fallback_card],
        "debug": debug,
    }


# ============================================
# 카드 조건 체크 함수
# ============================================

def _should_show_survival_card(scores: Dict, state_payload: Dict, debug: Dict) -> bool:
    """생존선 복구 카드 조건"""
    revenue_score = scores.get("revenue", 50)
    
    # revenue_score <= 35이면 무조건 표시
    if revenue_score <= 35:
        return True
    
    # 손익분기점 정보 확인 (추가 검증)
    try:
        # state_payload에서 period 정보 추출
        period = state_payload.get("period", {})
        year = period.get("year")
        month = period.get("month")
        
        # evidence에서 손익분기점 정보 확인
        evidence = state_payload.get("evidence", [])
        for ev in evidence:
            if "손익분기점" in ev.get("title", "") or "예상 매출" in ev.get("title", ""):
                note = ev.get("note", "")
                if "대비" in note:
                    # 비율 추출 시도
                    try:
                        ratio_str = note.split("대비")[1].split("%")[0].strip()
                        ratio = float(ratio_str) / 100.0
                        if ratio < 0.95:
                            return True
                    except Exception:
                        pass
        
        return False
    except Exception:
        return revenue_score <= 35


def _should_show_menu_profit_card(design_insights: Dict, design_state: Dict, debug: Dict) -> bool:
    """마진 구조 복구 카드 조건"""
    menu_portfolio = design_insights.get("menu_portfolio", {})
    menu_profit = design_insights.get("menu_profit", {})
    
    # 마진 메뉴 0개
    margin_count = menu_portfolio.get("margin_menu_count", 0)
    if margin_count == 0 and menu_portfolio.get("has_data"):
        return True
    
    # 고원가율 메뉴 다수
    high_cogs_count = menu_profit.get("high_cogs_ratio_menu_count", 0)
    if high_cogs_count >= 3 and menu_profit.get("has_data"):
        return True
    
    # 설계 상태 점수 낮음
    menu_profit_state = design_state.get("menu_profit", {})
    if menu_profit_state.get("score", 50) < 40:
        return True
    
    return False


def _should_show_ingredient_card(design_insights: Dict, design_state: Dict, debug: Dict) -> bool:
    """원가 집중 분산 카드 조건"""
    ingredient = design_insights.get("ingredient_structure", {})
    ingredient_state = design_state.get("ingredient_structure", {})
    
    # TOP3 집중도 >= 70%
    top3_concentration = ingredient.get("top3_concentration", 0.0)
    if top3_concentration >= 0.70 and ingredient.get("has_data"):
        return True
    
    # 고위험 재료 존재
    high_risk_count = ingredient.get("high_risk_ingredient_count", 0)
    if high_risk_count > 0 and ingredient.get("has_data"):
        return True
    
    # 설계 상태 점수 낮음
    if ingredient_state.get("score", 50) < 40:
        return True
    
    return False


def _should_show_portfolio_card(design_insights: Dict, design_state: Dict, debug: Dict) -> bool:
    """포트폴리오 재배치 카드 조건"""
    menu_portfolio = design_insights.get("menu_portfolio", {})
    menu_portfolio_state = design_state.get("menu_portfolio", {})
    
    # 유인메뉴 0 (간접: 마진 메뉴 0 또는 역할 미분류 과다)
    margin_count = menu_portfolio.get("margin_menu_count", 0)
    unclassified_ratio = menu_portfolio.get("role_unclassified_ratio", 0.0)
    
    if margin_count == 0 and menu_portfolio.get("has_data"):
        return True
    
    if unclassified_ratio >= 30.0 and menu_portfolio.get("has_data"):
        return True
    
    # 균형 점수 < 40
    balance_score = menu_portfolio.get("portfolio_balance_score", 0)
    if balance_score < 40 and menu_portfolio.get("has_data"):
        return True
    
    # 설계 상태 점수 낮음
    if menu_portfolio_state.get("score", 50) < 40:
        return True
    
    return False


def _should_show_sales_recovery_card(scores: Dict, state_payload: Dict, debug: Dict) -> bool:
    """매출 하락 원인 찾기 카드 조건"""
    sales_score = scores.get("sales", 50)
    
    # sales_score <= 45
    if sales_score <= 45:
        return True
    
    # 하락 신호 존재
    signals = state_payload.get("signals", [])
    for signal in signals:
        if signal.get("key", "").startswith("sales_") and signal.get("status") in ["warn", "risk"]:
            return True
    
    return False


# ============================================
# 카드 빌드 함수
# ============================================

def _build_survival_card(store_id: str, year: int, month: int, state_payload: Dict, design_insights: Dict) -> Optional[Dict]:
    """생존선 복구 카드"""
    try:
        from src.storage_supabase import calculate_break_even_sales, load_monthly_sales_total
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
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
        
        ratio = (expected_sales / break_even) if break_even > 0 else 0.0
        gap = break_even - expected_sales if expected_sales < break_even else 0
        
        # evidence에서 정보 추출 (없으면 계산값 사용)
        evidence_list = []
        state_evidence = state_payload.get("evidence", [])
        for ev in state_evidence:
            if "손익분기점" in ev.get("title", ""):
                evidence_list.append(f"손익분기점 {ev.get('value', '')}")
            elif "예상 매출" in ev.get("title", ""):
                note = ev.get("note", "")
                if "대비" in note:
                    evidence_list.append(note)
        
        if not evidence_list:
            evidence_list = [
                f"손익분기점 대비 {ratio*100:.0f}%",
                f"부족액 {gap:,.0f}원" if gap > 0 else "수익 구조 점수 낮음"
            ]
        
        return {
            "title": "생존선부터 복구하기",
            "goal": "예상 매출이 손익분기점을 넘도록 고정비/변동비 구조를 점검합니다.",
            "why": f"예상 매출({expected_sales:,.0f}원)이 손익분기점({break_even:,.0f}원)보다 {gap:,.0f}원 낮습니다." if gap > 0 else f"예상 매출이 손익분기점 대비 {ratio*100:.0f}%입니다.",
            "evidence": evidence_list[:2],
            "cta": {
                "label": "손익분기점부터 복구",
                "page": "수익 구조 설계실",
                "params": {}
            }
        }
    except Exception:
        return {
            "title": "생존선부터 복구하기",
            "goal": "손익분기점을 넘기기 위해 수익 구조를 점검합니다.",
            "why": "예상 매출이 손익분기점보다 낮습니다.",
            "evidence": ["수익 구조 점수 낮음"],
            "cta": {
                "label": "손익분기점부터 복구",
                "page": "수익 구조 설계실",
                "params": {}
            }
        }


def _build_menu_profit_card(store_id: str, design_insights: Dict, design_state: Dict) -> Optional[Dict]:
    """마진 구조 복구 카드"""
    menu_portfolio = design_insights.get("menu_portfolio", {})
    menu_profit = design_insights.get("menu_profit", {})
    
    margin_count = menu_portfolio.get("margin_menu_count", 0)
    high_cogs_count = menu_profit.get("high_cogs_ratio_menu_count", 0)
    worst_cogs = menu_profit.get("worst_cogs_ratio", 0.0)
    
    if margin_count == 0:
        return {
            "title": "마진 메뉴 만들기",
            "goal": "마진 메뉴가 없어 수익 기여도가 낮습니다. 가격/원가 구조를 점검합니다.",
            "why": f"마진 메뉴 0개 (전체 {menu_portfolio.get('has_data', False) and '메뉴 있음' or '데이터 부족'})",
            "evidence": [
                "마진 메뉴 0개",
                "수익 기여도 낮음"
            ],
            "cta": {
                "label": "가격/마진 후보 보기",
                "page": "메뉴 수익 구조 설계실",
                "params": {"tab": "execute"}
            }
        }
    elif high_cogs_count >= 3:
        return {
            "title": "고원가율 메뉴 정리",
            "goal": "고원가율 메뉴가 많아 수익 구조가 불안정합니다.",
            "why": f"고원가율(35% 이상) 메뉴 {high_cogs_count}개, 최악 원가율 {worst_cogs:.0f}%",
            "evidence": [
                f"고원가율 메뉴 {high_cogs_count}개",
                f"최악 원가율 {worst_cogs:.0f}%"
            ],
            "cta": {
                "label": "가격/마진 후보 보기",
                "page": "메뉴 수익 구조 설계실",
                "params": {"tab": "execute"}
            }
        }
    else:
        return {
            "title": "메뉴 수익 구조 점검",
            "goal": "메뉴 수익 구조를 최적화합니다.",
            "why": "메뉴 수익 구조 점수가 낮습니다.",
            "evidence": ["수익 구조 점수 낮음"],
            "cta": {
                "label": "가격/마진 후보 보기",
                "page": "메뉴 수익 구조 설계실",
                "params": {"tab": "execute"}
            }
        }


def _build_ingredient_card(store_id: str, design_insights: Dict, design_state: Dict) -> Optional[Dict]:
    """원가 집중 분산 카드"""
    ingredient = design_insights.get("ingredient_structure", {})
    
    top3_concentration = ingredient.get("top3_concentration", 0.0)
    high_risk_count = ingredient.get("high_risk_ingredient_count", 0)
    missing_substitute = ingredient.get("missing_substitute_count", 0)
    
    if top3_concentration >= 0.70:
        return {
            "title": "원가 집중도 분산",
            "goal": "상위 3개 재료에 과도하게 집중되어 있습니다. 대체재와 발주 구조를 설계합니다.",
            "why": f"TOP3 재료 집중도 {top3_concentration*100:.0f}%, 대체재 미설정 {missing_substitute}개",
            "evidence": [
                f"TOP3 집중도 {top3_concentration*100:.0f}%",
                f"대체재 미설정 {missing_substitute}개"
            ],
            "cta": {
                "label": "대체재/발주 구조 설계",
                "page": "재료 등록",
                "params": {"tab": "execute"}
            }
        }
    elif high_risk_count > 0:
        return {
            "title": "고위험 재료 점검",
            "goal": "고위험 재료가 확인되었습니다. 대체재와 발주 구조를 설계합니다.",
            "why": f"고위험 재료 {high_risk_count}개",
            "evidence": [
                f"고위험 재료 {high_risk_count}개",
                "대체재 설계 필요"
            ],
            "cta": {
                "label": "대체재/발주 구조 설계",
                "page": "재료 등록",
                "params": {"tab": "execute"}
            }
        }
    else:
        return {
            "title": "재료 구조 점검",
            "goal": "재료 구조를 최적화합니다.",
            "why": "재료 구조 점수가 낮습니다.",
            "evidence": ["재료 구조 점수 낮음"],
            "cta": {
                "label": "대체재/발주 구조 설계",
                "page": "재료 등록",
                "params": {"tab": "execute"}
            }
        }


def _build_portfolio_card(store_id: str, design_insights: Dict, design_state: Dict) -> Optional[Dict]:
    """포트폴리오 재배치 카드"""
    menu_portfolio = design_insights.get("menu_portfolio", {})
    
    margin_count = menu_portfolio.get("margin_menu_count", 0)
    unclassified_ratio = menu_portfolio.get("role_unclassified_ratio", 0.0)
    balance_score = menu_portfolio.get("portfolio_balance_score", 0)
    
    if margin_count == 0:
        return {
            "title": "마진 메뉴 지정하기",
            "goal": "마진 메뉴가 없어 포트폴리오 균형이 깨졌습니다.",
            "why": f"마진 메뉴 0개",
            "evidence": [
                "마진 메뉴 0개",
                "포트폴리오 균형 불량"
            ],
            "cta": {
                "label": "역할/카테고리 정리",
                "page": "메뉴 등록",
                "params": {"tab": "execute"}
            }
        }
    elif unclassified_ratio >= 30.0:
        return {
            "title": "메뉴 역할 분류하기",
            "goal": "미분류 메뉴가 많아 포트폴리오 전략이 불명확합니다.",
            "why": f"미분류 메뉴 {unclassified_ratio:.0f}%",
            "evidence": [
                f"미분류 비율 {unclassified_ratio:.0f}%",
                "역할 분류 필요"
            ],
            "cta": {
                "label": "역할/카테고리 정리",
                "page": "메뉴 등록",
                "params": {"tab": "execute"}
            }
        }
    else:
        return {
            "title": "포트폴리오 균형 개선",
            "goal": "포트폴리오 균형 점수를 개선합니다.",
            "why": f"균형 점수 {balance_score}점",
            "evidence": [
                f"균형 점수 {balance_score}점",
                "재배치 필요"
            ],
            "cta": {
                "label": "역할/카테고리 정리",
                "page": "메뉴 등록",
                "params": {"tab": "execute"}
            }
        }


def _build_sales_recovery_card(store_id: str, scores: Dict, state_payload: Dict) -> Optional[Dict]:
    """매출 하락 원인 찾기 카드"""
    sales_score = scores.get("sales", 50)
    
    # 하락 신호 찾기
    signals = state_payload.get("signals", [])
    sales_signal = None
    for signal in signals:
        if signal.get("key", "").startswith("sales_"):
            sales_signal = signal
            break
    
    if sales_signal:
        value = sales_signal.get("value", "")
        return {
            "title": "매출 하락 원인 찾기",
            "goal": "매출이 하락 중입니다. 원인을 빠르게 파악합니다.",
            "why": f"매출 점수 {sales_score:.0f}점, {sales_signal.get('note', '')}",
            "evidence": [
                f"매출 점수 {sales_score:.0f}점",
                value
            ],
            "cta": {
                "label": "원인 1분 진단",
                "page": "매출 하락 원인 찾기",
                "params": {}
            }
        }
    else:
        return {
            "title": "매출 하락 원인 찾기",
            "goal": "매출이 하락 중입니다. 원인을 빠르게 파악합니다.",
            "why": f"매출 점수 {sales_score:.0f}점",
            "evidence": [
                f"매출 점수 {sales_score:.0f}점",
                "하락 신호 확인"
            ],
            "cta": {
                "label": "원인 1분 진단",
                "page": "매출 하락 원인 찾기",
                "params": {}
            }
        }


def _build_fallback_card(store_id: Optional[str]) -> Dict:
    """Fallback 카드 (데이터 부족 시)"""
    return {
        "title": "설계부터 채우기",
        "goal": "데이터가 부족합니다. 먼저 설계 데이터를 채워주세요.",
        "why": "설계 데이터 부족으로 전략을 생성할 수 없습니다.",
        "evidence": [
            "데이터 부족",
            "설계 센터에서 시작"
        ],
        "cta": {
            "label": "설계부터 채우기",
            "page": "가게 설계 센터",
            "params": {}
        }
    }


def _build_strategy_cards_v4(
    store_id: str,
    year: int,
    month: int,
    state_payload: Optional[Dict],
    debug: Dict
) -> Dict:
    """
    v4 전략 카드 생성 (건강검진 통합)
    """
    try:
        from src.health_check.profile import load_latest_health_profile
        from src.strategy.v4_strategy_engine import build_base_strategies
        from src.strategy.health_weighting import apply_health_weighting
        
        # 1. 가게 상태 분류 (없으면 호출)
        if state_payload is None:
            state_payload = classify_store_state(store_id, year, month)
        
        store_state = state_payload.get("state", {})
        scores = state_payload.get("scores", {})
        state_code = store_state.get("code", "unknown")
        
        # 2. 건강검진 데이터 로드 (v4: 판독 결과 직접 사용)
        from ui_pages.home.home_data import load_latest_health_diag
        from src.health_check.health_integration import health_bias_for_card, should_show_operation_qsc_card
        
        health_diag = load_latest_health_diag(store_id)
        health_profile = load_latest_health_profile(store_id, lookback_days=60)
        
        if health_diag:
            debug["rules_fired"].append("건강검진 판독 데이터 로드됨")
        elif health_profile.get("exists"):
            debug["rules_fired"].append("건강검진 프로필 로드됨 (판독 없음)")
        
        # 3. 컨텍스트 구성
        from src.storage_supabase import calculate_break_even_sales, load_monthly_sales_total
        from ui_pages.design_lab.design_insights import get_design_insights
        
        monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
        break_even = calculate_break_even_sales(store_id, year, month) or 1
        break_even_gap_ratio = (monthly_sales / break_even) if break_even > 0 else 1.0
        
        design_insights = get_design_insights(store_id, year, month)
        menu_portfolio = design_insights.get("menu_portfolio", {})
        margin_menu_count = menu_portfolio.get("margin_menu_count", 0)
        total_menu_count = menu_portfolio.get("total_menu_count", 1)
        margin_menu_ratio = margin_menu_count / total_menu_count if total_menu_count > 0 else 0.0
        
        ingredient = design_insights.get("ingredient_structure", {})
        ingredient_concentration = ingredient.get("top3_concentration", 0.0)
        
        # 방문자 추세 (간단히)
        visitors_trend = "unknown"
        try:
            from src.storage_supabase import load_best_available_daily_sales
            from datetime import date, timedelta
            today = date.today()
            week_ago = today - timedelta(days=7)
            recent_sales = load_best_available_daily_sales(
                store_id=store_id,
                start_date=week_ago.isoformat(),
                end_date=today.isoformat()
            )
            if not recent_sales.empty and len(recent_sales) >= 2:
                recent_avg = recent_sales.tail(3)['total_sales'].mean() if 'total_sales' in recent_sales.columns else 0
                older_avg = recent_sales.head(3)['total_sales'].mean() if len(recent_sales) >= 6 else recent_avg
                if recent_avg > older_avg * 1.1:
                    visitors_trend = "up"
                elif recent_avg < older_avg * 0.9:
                    visitors_trend = "down"
                else:
                    visitors_trend = "stable"
        except Exception:
            pass
        
        context = {
            "store_state": store_state,
            "overall_score": scores.get("overall", 50),
            "break_even_gap_ratio": break_even_gap_ratio,
            "margin_menu_ratio": margin_menu_ratio,
            "ingredient_concentration": ingredient_concentration,
            "visitors_trend": visitors_trend
        }
        
        # 4. 기본 전략 생성
        base_strategies = build_base_strategies(context)
        debug["rules_fired"].append(f"기본 전략 {len(base_strategies)}개 생성")
        
        # 5. 건강검진 가중치 적용 (v4: health_diag 직접 사용)
        if health_diag:
            # health_diag 기반 가중치 적용
            w_health = 0.30  # 검진 가중치 (30%)
            
            for strategy in base_strategies:
                strategy_type = strategy.get("type", "")
                
                # 카드 코드 매핑 (v4_strategy_engine의 StrategyType → 카드 코드)
                type_to_card_code = {
                    "SURVIVAL": "FINANCE_SURVIVAL_LINE",
                    "MARGIN": "MENU_MARGIN_RECOVERY",
                    "COST": "INGREDIENT_RISK_DIVERSIFY",
                    "PORTFOLIO": "MENU_PORTFOLIO_REBALANCE",
                    "ACQUISITION": "SALES_DROP_INVESTIGATION",
                    "OPERATIONS": "OPERATION_QSC_RECOVERY"
                }
                
                card_code = type_to_card_code.get(strategy_type, "")
                if card_code:
                    health_bias = health_bias_for_card(card_code, health_diag)
                    # priority_score에 health_bias 반영
                    base_priority = strategy.get("priority_score", 100)
                    strategy["priority_score"] = base_priority + (w_health * health_bias * 100)
                    
                    # OPERATION_QSC_RECOVERY 카드 강화
                    if card_code == "OPERATION_QSC_RECOVERY" and should_show_operation_qsc_card(health_diag):
                        strategy["title"] = "운영 품질(QSC) 복구부터 하세요"
                        strategy["reasons"] = [
                            "H/S/C 축 동시 저하 → 재방문 붕괴 위험",
                            "이번 주 운영 개선 TOP3 실행"
                        ]
                        strategy["priority_score"] = base_priority + (w_health * 1.0 * 100)  # 최대 가중치
            
            debug["rules_fired"].append("건강검진 판독 가중치 적용됨")
            final_strategies = base_strategies
        else:
            # health_diag가 없으면 기존 health_weighting 사용
            final_strategies = apply_health_weighting(base_strategies, health_profile)
            if health_profile.get("exists"):
                debug["rules_fired"].append("건강검진 프로필 가중치 적용됨")
        
        # 6. Impact 및 Action Plan 계산
        from src.strategy.impact_engine import estimate_impact
        from src.strategy.action_plan_engine import build_action_plan
        
        # 컨텍스트 확장 (impact/action_plan 계산용)
        # KPI 추가 로드
        from datetime import date, timedelta
        from zoneinfo import ZoneInfo
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        today = now.date()
        yesterday = today - timedelta(days=1)
        
        # 어제 매출
        yesterday_sales = 0
        try:
            from src.storage_supabase import load_best_available_daily_sales
            yesterday_df = load_best_available_daily_sales(
                store_id=store_id,
                start_date=yesterday.isoformat(),
                end_date=yesterday.isoformat()
            )
            if not yesterday_df.empty and 'total_sales' in yesterday_df.columns:
                yesterday_sales = int(float(yesterday_df.iloc[0]['total_sales'] or 0))
        except Exception:
            pass
        
        # 방문자 데이터 (간단히)
        visitors_mtd = 0
        sales_per_visitor = 0
        try:
            from src.auth import get_supabase_client
            supabase = get_supabase_client()
            if supabase:
                # MTD 방문자 합계
                month_start = date(year, month, 1)
                if month == 12:
                    month_end = date(year + 1, 1, 1)
                else:
                    month_end = date(year, month + 1, 1)
                
                visitors_result = supabase.table("naver_visitors").select("visitors").eq(
                    "store_id", store_id
                ).gte("date", month_start.isoformat()).lt("date", month_end.isoformat()).execute()
                
                if visitors_result.data:
                    visitors_mtd = sum(int(r.get("visitors", 0)) for r in visitors_result.data)
                    if visitors_mtd > 0 and monthly_sales > 0:
                        sales_per_visitor = monthly_sales / visitors_mtd
        except Exception:
            pass
        
        # 경과 일수 계산 (MTD 매출 추정용)
        if now.year == year and now.month == month:
            month_start_date = date(year, month, 1)
            elapsed_days = max(1, (today - month_start_date).days + 1)
        else:
            elapsed_days = 30
        
        full_context = {
            "store_id": store_id,
            "period": {"year": year, "month": month},
            "kpi": {
                "mtd_sales": monthly_sales,
                "avg_daily_sales": monthly_sales / elapsed_days if elapsed_days > 0 else 0,
                "yesterday_sales": yesterday_sales,
                "visitors_mtd": visitors_mtd,
                "sales_per_visitor": sales_per_visitor
            },
            "revenue": {
                "break_even_sales": break_even,
                "break_even_gap_ratio": break_even_gap_ratio,
                "variable_cost_rate": None,  # impact_engine에서 계산
                "fixed_cost": None
            },
            "menu": {
                "avg_food_cost_rate": None,
                "high_cost_menu_count": menu_portfolio.get("high_cogs_ratio_menu_count", 0),
                "margin_menu_ratio": margin_menu_ratio
            },
            "ingredient": {
                "top3_cost_concentration_pct": ingredient_concentration * 100 if ingredient_concentration else None
            },
            "health": health_profile
        }
        
        # 각 전략에 impact와 action_plan 추가
        for strategy in final_strategies:
            strategy_type = strategy.get("type", "")
            
            # Impact 계산
            try:
                impact = estimate_impact(strategy_type, full_context)
                strategy["impact"] = impact
            except Exception as e:
                debug["notes"].append(f"Impact 계산 오류 ({strategy_type}): {str(e)}")
                strategy["impact"] = {"won": None, "kind": "indirect", "assumptions": ["계산 오류"], "confidence": 0.3}
            
            # Action Plan 생성
            try:
                action_plan = build_action_plan(strategy_type, full_context)
                strategy["action_plan"] = action_plan
            except Exception as e:
                debug["notes"].append(f"Action Plan 생성 오류 ({strategy_type}): {str(e)}")
                strategy["action_plan"] = _get_empty_action_plan()
        
        # 7. priority_score로 정렬하여 TOP3 선택
        final_strategies_sorted = sorted(
            final_strategies,
            key=lambda s: s.get("priority_score", 0),
            reverse=True
        )
        
        # 8. v1 형식으로 변환 (TOP3)
        cards = []
        for idx, strategy in enumerate(final_strategies_sorted[:3], 1):
            # 검진 근거 추가 (health_diag가 있을 때)
            reasons = strategy.get("reasons", [])
            if health_diag and idx == 1:  # 1순위 카드에만 검진 근거 추가
                from src.health_check.health_integration import get_health_evidence_line
                health_evidence = get_health_evidence_line(health_diag)
                if health_evidence:
                    # 기존 reasons에 검진 근거 추가 (최대 1개)
                    reasons = reasons[:1] + [health_evidence] if reasons else [health_evidence]
            
            card = {
                "rank": idx,
                "title": strategy.get("title", ""),
                "goal": reasons[0] if reasons else "",
                "why": " | ".join(reasons[:2]),
                "evidence": reasons[:3],
                "type": strategy.get("type", ""),  # CTA 매핑용
                "cta": {
                    "label": strategy.get("cta", {}).get("label", "실행하기"),
                    "page": strategy.get("cta", {}).get("page_key", ""),
                    "params": strategy.get("cta", {}).get("params", {})
                },
                "impact": strategy.get("impact", {}),
                "action_plan": strategy.get("action_plan", {}),
                "success_prob": strategy.get("success_prob", 0.55)
            }
            cards.append(card)
        
        return {
            "period": {"year": year, "month": month},
            "store_state": {
                "code": state_code,
                "label": store_state.get("label", ""),
                "scores": scores,
            },
            "cards": cards,
            "debug": debug,
        }
    
    except Exception as e:
        debug["notes"].append(f"v4 카드 생성 오류: {str(e)}")
        # Fallback: 기존 v1 엔진 사용
        return _build_strategy_cards_v1_fallback(store_id, year, month, state_payload, debug)


def _build_strategy_cards_v1_fallback(
    store_id: str,
    year: int,
    month: int,
    state_payload: Optional[Dict],
    debug: Dict
) -> Dict:
    """v1 엔진 fallback (기존 로직 재사용)"""
    # 기존 v1 로직 실행 (아래 코드 블록 재사용)
    try:
        # 1. 가게 상태 분류 (없으면 호출)
        if state_payload is None:
            state_payload = classify_store_state(store_id, year, month)
        
        store_state = state_payload.get("state", {})
        scores = state_payload.get("scores", {})
        state_code = store_state.get("code", "unknown")
        
        # 2. 설계 인사이트 로드
        design_insights = get_design_insights(store_id, year, month)
        design_state = get_design_state(store_id, year, month)
        
        # 3. 카드 후보 생성
        candidate_cards = []
        
        # 카드 1: 생존선 복구 (Revenue)
        if _should_show_survival_card(scores, state_payload, debug):
            card = _build_survival_card(store_id, year, month, state_payload, design_insights)
            if card:
                candidate_cards.append(("survival", card))
                debug["rules_fired"].append("생존선 복구 카드")
        
        # 카드 2: 마진 구조 복구 (Menu Profit)
        if _should_show_menu_profit_card(design_insights, design_state, debug):
            card = _build_menu_profit_card(store_id, design_insights, design_state)
            if card:
                candidate_cards.append(("menu_profit", card))
                debug["rules_fired"].append("마진 구조 복구 카드")
        
        # 카드 3: 원가 집중 분산 (Ingredient)
        if _should_show_ingredient_card(design_insights, design_state, debug):
            card = _build_ingredient_card(store_id, design_insights, design_state)
            if card:
                candidate_cards.append(("ingredient", card))
                debug["rules_fired"].append("원가 집중 분산 카드")
        
        # 카드 4: 포트폴리오 재배치 (Portfolio)
        if _should_show_portfolio_card(design_insights, design_state, debug):
            card = _build_portfolio_card(store_id, design_insights, design_state)
            if card:
                candidate_cards.append(("portfolio", card))
                debug["rules_fired"].append("포트폴리오 재배치 카드")
        
        # 카드 5: 매출 하락 원인 찾기 (Sales Recovery)
        if _should_show_sales_recovery_card(scores, state_payload, debug):
            card = _build_sales_recovery_card(store_id, scores, state_payload)
            if card:
                candidate_cards.append(("sales_recovery", card))
                debug["rules_fired"].append("매출 하락 원인 찾기 카드")
        
        # 4. 우선순위 정렬 및 중복 제거
        selected_cards = _select_top3_cards(candidate_cards, debug)
        
        # 5. 3장 미만이면 Fallback으로 채움
        while len(selected_cards) < 3:
            fallback_card = _build_fallback_card(store_id)
            selected_cards.append(fallback_card)
            debug["rules_fired"].append("Fallback 카드")
        
        # 6. rank 부여
        for idx, card in enumerate(selected_cards[:3], 1):
            card["rank"] = idx
        
        return {
            "period": {"year": year, "month": month},
            "store_state": {
                "code": state_code,
                "label": store_state.get("label", ""),
                "scores": scores,
            },
            "cards": selected_cards[:3],
            "debug": debug,
        }
    except Exception as e:
        debug["notes"].append(f"v1 fallback 오류: {str(e)}")
        return _get_empty_cards(year, month, debug)


def _get_empty_action_plan() -> Dict:
    """빈 action plan 반환"""
    return {
        "time_horizon": "1주",
        "difficulty": "중간",
        "steps": [],
        "watchouts": [],
        "required_pages": []
    }


def _select_top3_cards(candidate_cards: List[tuple], debug: Dict) -> List[Dict]:
    """
    카드 우선순위 정렬 및 중복 제거
    
    우선순위:
    1. survival
    2. menu_profit
    3. ingredient
    4. portfolio
    5. sales_recovery
    """
    priority_order = ["survival", "menu_profit", "ingredient", "portfolio", "sales_recovery"]
    
    # 우선순위별로 정렬
    sorted_cards = []
    for priority in priority_order:
        for card_type, card in candidate_cards:
            if card_type == priority:
                sorted_cards.append(card)
                break
    
    # 중복 CTA/page 제거 (같은 page는 첫 번째만)
    seen_pages = set()
    unique_cards = []
    for card in sorted_cards:
        page = card.get("cta", {}).get("page", "")
        if page and page not in seen_pages:
            unique_cards.append(card)
            seen_pages.add(page)
        elif not page:
            unique_cards.append(card)
    
    return unique_cards[:3]
