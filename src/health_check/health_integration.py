"""
건강검진 통합 헬퍼 모듈
HOME/전략 엔진에서 검진 데이터를 활용하기 위한 헬퍼 함수들
"""

import logging
from typing import Dict, Optional, List
from src.health_check.storage import (
    get_health_diagnosis,
    get_health_results,
    get_health_session
)
from src.health_check.health_diagnosis_engine import diagnose_health_check
from src.auth import get_supabase_client, get_current_store_id

logger = logging.getLogger(__name__)


def get_health_diag_for_home(store_id: str) -> Optional[Dict]:
    """
    HOME에서 사용할 최신 완료 검진 판독 데이터 로드
    
    Process:
    1. 최신 완료 검진 세션 조회
    2. 이미 DB에 판독 결과가 있으면 그것을 반환
    3. 없으면 점수 결과를 로드하여 판독 실행 후 저장
    
    Args:
        store_id: 매장 ID
    
    Returns:
        {
            "risk_axes": [...],
            "primary_pattern": {...},
            "insight_summary": [...],
            "strategy_bias": {...}
        } or None
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.debug("get_health_diag_for_home: Supabase client not available")
            return None
        
        # 최신 완료 검진 세션 조회
        result = supabase.table("health_check_sessions").select(
            "id, completed_at, overall_score, overall_grade, diagnosis_json"
        ).eq("store_id", store_id).not_.is_("completed_at", "null").order(
            "completed_at", desc=True
        ).limit(1).execute()
        
        if not result.data:
            logger.debug("get_health_diag_for_home: No completed health check found")
            return None
        
        from src.ui_helpers import safe_resp_first_data
        session = safe_resp_first_data(result)
        session_id = session["id"]
        
        # 이미 판독 결과가 있으면 반환
        diagnosis_json = session.get("diagnosis_json")
        if diagnosis_json:
            # JSONB가 dict로 반환되는 경우와 문자열인 경우 모두 처리
            if isinstance(diagnosis_json, dict):
                return diagnosis_json
            elif isinstance(diagnosis_json, str):
                import json
                return json.loads(diagnosis_json)
        
        # 판독 결과가 없으면 생성
        logger.info(f"get_health_diag_for_home: Generating diagnosis for session {session_id}")
        
        # 검진 결과 로드
        results = get_health_results(session_id)
        if not results:
            logger.warning("get_health_diag_for_home: No health results found")
            return None
        
        # axis_scores 구성
        axis_scores = {}
        for r in results:
            category = r.get("category")
            score_avg = r.get("score_avg")
            if category and score_avg is not None:
                axis_scores[category] = float(score_avg)
        
        if not axis_scores:
            logger.warning("get_health_diag_for_home: No axis scores found")
            return None
        
        # 판독 실행
        diagnosis = diagnose_health_check(
            session_id=session_id,
            store_id=store_id,
            axis_scores=axis_scores,
            axis_raw=None,
            meta=None
        )
        
        # DB에 저장 (다음 번에는 재사용)
        try:
            import json
            supabase.table("health_check_sessions").update({
                "diagnosis_json": json.dumps(diagnosis, ensure_ascii=False)
            }).eq("id", session_id).execute()
        except Exception as e:
            logger.warning(f"get_health_diag_for_home: Failed to save diagnosis_json: {e}")
        
        return diagnosis
    
    except Exception as e:
        logger.error(f"get_health_diag_for_home: Error - {e}")
        return None


def health_bias_for_card(card_code: str, health_diag: Optional[Dict]) -> float:
    """
    전략 카드 코드에 대한 검진 기반 가중치 계산
    
    Args:
        card_code: 전략 카드 코드
            - "FINANCE_SURVIVAL_LINE"
            - "MENU_MARGIN_RECOVERY"
            - "MENU_PORTFOLIO_REBALANCE"
            - "INGREDIENT_RISK_DIVERSIFY"
            - "SALES_DROP_INVESTIGATION"
            - "OPERATION_QSC_RECOVERY"
        health_diag: 검진 판독 결과 (None 가능)
    
    Returns:
        가중치 (0.0 ~ 1.0)
    """
    if not health_diag:
        return 0.0
    
    # strategy_bias에서 직접 매핑
    strategy_bias = health_diag.get("strategy_bias", {})
    
    # 카드 코드 → strategy_bias 키 매핑
    card_to_bias_map = {
        "FINANCE_SURVIVAL_LINE": "finance_control",
        "MENU_MARGIN_RECOVERY": "pricing",
        "MENU_PORTFOLIO_REBALANCE": "menu_structure",
        "INGREDIENT_RISK_DIVERSIFY": "menu_structure",  # 재료 구조도 메뉴 구조에 포함
        "SALES_DROP_INVESTIGATION": "marketing",  # 마케팅 카드가 없으므로 매출 조사에 소량 반영
        "OPERATION_QSC_RECOVERY": "operation_fix"
    }
    
    bias_key = card_to_bias_map.get(card_code)
    if bias_key and bias_key in strategy_bias:
        base_bias = strategy_bias[bias_key]
    else:
        base_bias = 0.0
    
    # 추가 규칙: primary_pattern / risk_axes 기반 보정
    primary_pattern = health_diag.get("primary_pattern", {})
    pattern_code = primary_pattern.get("code", "")
    
    risk_axes = health_diag.get("risk_axes", [])
    high_risk_axes = [r["axis"] for r in risk_axes if r.get("level") == "high"]
    
    # OPERATION_QSC_RECOVERY 카드 강화
    if card_code == "OPERATION_QSC_RECOVERY":
        # H/S/C 중 2개 이상이 high면 추가 가중치
        hsc_high_count = sum(1 for axis in high_risk_axes if axis in ["H", "S", "C"])
        if hsc_high_count >= 2:
            base_bias = min(1.0, base_bias + 0.3)
        
        # OPERATION_BREAKDOWN 또는 REVISIT_COLLAPSE 패턴이면 추가 가중치
        if pattern_code in ["OPERATION_BREAKDOWN", "REVISIT_COLLAPSE"]:
            base_bias = min(1.0, base_bias + 0.2)
    
    # FINANCE_SURVIVAL_LINE / MENU_MARGIN_RECOVERY 카드 강화
    elif card_code in ["FINANCE_SURVIVAL_LINE", "MENU_MARGIN_RECOVERY"]:
        # P1/F가 high면 추가 가중치
        if "P1" in high_risk_axes or "F" in high_risk_axes:
            base_bias = min(1.0, base_bias + 0.2)
    
    # MENU_PORTFOLIO_REBALANCE 카드 강화
    elif card_code == "MENU_PORTFOLIO_REBALANCE":
        # P2/P3가 high면 소량 추가
        if "P2" in high_risk_axes or "P3" in high_risk_axes:
            base_bias = min(1.0, base_bias + 0.1)
    
    # SALES_DROP_INVESTIGATION 카드 강화
    elif card_code == "SALES_DROP_INVESTIGATION":
        # M이 high면 소량 추가
        if "M" in high_risk_axes:
            base_bias = min(1.0, base_bias + 0.15)
    
    return base_bias


def should_show_operation_qsc_card(health_diag: Optional[Dict]) -> bool:
    """
    OPERATION_QSC_RECOVERY 카드 발동 조건 확인
    
    Args:
        health_diag: 검진 판독 결과
    
    Returns:
        카드를 표시해야 하면 True
    """
    if not health_diag:
        return False
    
    primary_pattern = health_diag.get("primary_pattern", {})
    pattern_code = primary_pattern.get("code", "")
    
    risk_axes = health_diag.get("risk_axes", [])
    high_risk_axes = [r["axis"] for r in risk_axes if r.get("level") == "high"]
    
    # 조건 1: H/S/C 중 2개 이상이 high
    hsc_high_count = sum(1 for axis in high_risk_axes if axis in ["H", "S", "C"])
    if hsc_high_count >= 2:
        return True
    
    # 조건 2: primary_pattern이 OPERATION_BREAKDOWN 또는 REVISIT_COLLAPSE
    if pattern_code in ["OPERATION_BREAKDOWN", "REVISIT_COLLAPSE"]:
        return True
    
    return False


def get_health_evidence_line(health_diag: Optional[Dict]) -> Optional[str]:
    """
    검진 판독에서 evidence 문장 1개 추출
    
    Args:
        health_diag: 검진 판독 결과
    
    Returns:
        evidence 문장 또는 None
    """
    if not health_diag:
        return None
    
    insight_summary = health_diag.get("insight_summary", [])
    if insight_summary:
        # 첫 번째 문장 반환 (가장 핵심적인 판결)
        return insight_summary[0]
    
    return None
