"""
건강검진 시스템 Storage Layer
Supabase 기반 데이터 저장/조회
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from src.auth import get_supabase_client, get_current_store_id
from src.health_check.scoring import (
    score_from_raw,
    calc_category_score,
    compute_session_results,
    compute_strength_flags,
    compute_risk_flags
)
from src.health_check.questions_bank import CATEGORIES_ORDER, QUESTIONS
from src.health_check.health_diagnosis_engine import diagnose_health_check

logger = logging.getLogger(__name__)


def create_health_session(store_id: str, check_type: str = 'ad-hoc') -> tuple[Optional[str], Optional[str]]:
    """
    건강검진 세션 생성
    
    Args:
        store_id: 매장 ID
        check_type: 검진 유형 ('ad-hoc' | 'regular' | 'periodic' | 'monthly')
    
    Returns:
        (session_id, error_message) 튜플
        - 성공: (session_id, None)
        - 실패: (None, error_message)
    """
    try:
        if not store_id:
            return None, "매장 ID가 없습니다."
        
        supabase = get_supabase_client()
        if not supabase:
            error_msg = "Supabase 클라이언트를 생성할 수 없습니다. 로그인 상태를 확인해주세요."
            logger.error("create_health_session: Supabase client not available")
            return None, error_msg
        
        result = supabase.table("health_check_sessions").insert({
            "store_id": store_id,
            "check_type": check_type,
            "started_at": datetime.utcnow().isoformat() + "Z"
        }).execute()
        
        from src.ui_helpers import safe_resp_first_data
        session_data = safe_resp_first_data(result)
        if session_data:
            session_id = session_data.get('id')
            logger.info(f"create_health_session: Session created - {session_id}")
            return session_id, None
        else:
            error_msg = "세션 생성 후 데이터를 받지 못했습니다. 데이터베이스 상태를 확인해주세요."
            logger.error("create_health_session: No data returned from insert")
            return None, error_msg
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"create_health_session: Error - {e}", exc_info=True)
        
        # 에러 타입별 메시지 개선
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            return None, "건강검진 테이블이 생성되지 않았습니다. SQL 파일(health_check_phase1.sql)을 Supabase에서 실행해주세요."
        elif "permission denied" in error_msg.lower() or "policy" in error_msg.lower():
            return None, "데이터베이스 권한 문제가 있습니다. RLS 정책을 확인해주세요."
        elif "foreign key" in error_msg.lower():
            return None, f"매장 ID({store_id})가 유효하지 않습니다."
        elif "check constraint" in error_msg.lower() and "valid_check_type" in error_msg.lower():
            return None, f"검진 유형 '{check_type}'이 허용되지 않습니다. 허용된 값: 'ad-hoc', 'regular', 'periodic', 'monthly'. SQL 제약조건을 업데이트해주세요."
        else:
            return None, f"세션 생성 중 오류가 발생했습니다: {error_msg}"


def upsert_health_answers_batch(
    store_id: str,
    session_id: str,
    answers: List[Dict[str, str]]
) -> tuple[bool, Optional[str]]:
    """
    건강검진 답변 일괄 저장/업데이트
    
    Args:
        store_id: 매장 ID
        session_id: 세션 ID
        answers: 답변 리스트, 각 항목은 {"category": str, "question_code": str, "raw_value": str, "memo": Optional[str]}
    
    Returns:
        (성공 여부, 에러 메시지)
    """
    if not answers:
        return True, None
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Supabase client not available"
        
        # 답변 데이터 준비
        rows = []
        for ans in answers:
            category = ans.get('category')
            question_code = ans.get('question_code')
            raw_value = ans.get('raw_value')
            memo = ans.get('memo')
            
            if not category or not question_code or not raw_value:
                continue
            
            score = score_from_raw(raw_value)
            rows.append({
                "store_id": store_id,
                "session_id": session_id,
                "category": category,
                "question_code": question_code,
                "raw_value": raw_value,
                "score": score,
                "memo": memo,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            })
        
        if not rows:
            return False, "No valid answers to save"
        
        # 일괄 upsert
        result = supabase.table("health_check_answers").upsert(
            rows,
            on_conflict="store_id,session_id,category,question_code"
        ).execute()
        
        if result.data:
            logger.info(f"upsert_health_answers_batch: Saved {len(rows)} answers")
            return True, None
        else:
            return False, "No data returned from upsert"
    
    except Exception as e:
        logger.error(f"upsert_health_answers_batch: Error - {e}", exc_info=True)
        return False, str(e)


def upsert_health_answer(
    store_id: str,
    session_id: str,
    category: str,
    question_code: str,
    raw_value: str,
    memo: Optional[str] = None
) -> bool:
    """
    건강검진 답변 저장/업데이트
    
    Args:
        store_id: 매장 ID
        session_id: 세션 ID
        category: 카테고리 코드 ('Q', 'S', 'C', 'P1', 'P2', 'P3', 'M', 'H', 'F')
        question_code: 질문 코드 ('Q1', 'S1', 'P1_1' 등)
        raw_value: 원시 답변 ('yes' | 'maybe' | 'no')
        memo: 메모 (선택)
    
    Returns:
        성공 여부
    """
    try:
        # 점수 계산
        score = score_from_raw(raw_value)
        
        supabase = get_supabase_client()
        if not supabase:
            logger.error("upsert_health_answer: Supabase client not available")
            return False
        
        # upsert (unique constraint: store_id, session_id, category, question_code)
        result = supabase.table("health_check_answers").upsert({
            "store_id": store_id,
            "session_id": session_id,
            "category": category,
            "question_code": question_code,
            "raw_value": raw_value,
            "score": score,
            "memo": memo,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }, on_conflict="store_id,session_id,category,question_code").execute()
        
        if result.data:
            logger.debug(f"upsert_health_answer: Answer saved - {category}/{question_code}")
            return True
        else:
            logger.error("upsert_health_answer: No data returned from upsert")
            return False
    
    except Exception as e:
        logger.error(f"upsert_health_answer: Error - {e}")
        return False


def finalize_health_session(store_id: str, session_id: str) -> bool:
    """
    건강검진 세션 완료 처리 및 결과 계산/저장
    
    Args:
        store_id: 매장 ID
        session_id: 세션 ID
    
    Returns:
        성공 여부
    
    Process:
        1. answers 테이블에서 모든 답변 로드
        2. 카테고리별로 그룹화하여 점수 계산
        3. compute_session_results로 전체 결과 계산
        4. health_check_results 테이블에 카테고리별 결과 저장
        5. health_check_sessions 테이블에 overall_score/grade/main_bottleneck 업데이트
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.error("finalize_health_session: Supabase client not available")
            return False
        
        # 1. 답변 로드 (question_code 순서로 정렬)
        answers_result = supabase.table("health_check_answers").select(
            "category, question_code, score"
        ).eq("store_id", store_id).eq("session_id", session_id).order("question_code").execute()
        
        if not answers_result.data:
            logger.warning(f"finalize_health_session: No answers found for session {session_id}")
            # 답변이 없어도 세션은 완료 처리 (graceful fallback)
            supabase.table("health_check_sessions").update({
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "overall_score": 0.0,
                "overall_grade": "E",
                "main_bottleneck": None
            }).eq("id", session_id).execute()
            return True
        
        # 2. 카테고리별로 그룹화 (question_code 순서 유지)
        answers_by_category: Dict[str, List[int]] = {}
        for answer in answers_result.data:
            category = answer['category']
            score = answer['score']
            
            if category not in answers_by_category:
                answers_by_category[category] = []
            answers_by_category[category].append(score)
        
        # 3. 결과 계산
        results = compute_session_results(answers_by_category)
        
        # 3.5. 판독 엔진 실행 (경영 해석)
        axis_scores = {
            cat: data['score_avg']
            for cat, data in results['per_category'].items()
        }
        
        # raw answers 로드 (선택적, 판독 엔진에서 사용 가능)
        axis_raw = {}
        answers_raw_result = supabase.table("health_check_answers").select(
            "category, question_code, raw_value"
        ).eq("store_id", store_id).eq("session_id", session_id).order("question_code").execute()
        
        for answer in answers_raw_result.data:
            category = answer['category']
            raw_value = answer['raw_value']
            if category not in axis_raw:
                axis_raw[category] = []
            axis_raw[category].append(raw_value)
        
        # 판독 실행
        diagnosis = diagnose_health_check(
            session_id=session_id,
            store_id=store_id,
            axis_scores=axis_scores,
            axis_raw=axis_raw if axis_raw else None,
            meta=None
        )
        
        # 4. health_check_results에 카테고리별 결과 저장
        for category, category_data in results['per_category'].items():
            # 해당 카테고리의 답변 리스트 가져오기
            category_answers = answers_by_category.get(category, [])
            
            # 강점/리스크 플래그 계산
            strength_flags = compute_strength_flags(category_answers, category)
            risk_flags = compute_risk_flags(category_answers, category)
            
            # upsert
            supabase.table("health_check_results").upsert({
                "store_id": store_id,
                "session_id": session_id,
                "category": category,
                "score_avg": category_data['score_avg'],
                "risk_level": category_data['risk_level'],
                "strength_flags": strength_flags,
                "risk_flags": risk_flags,
                "structure_summary": None,  # 나중에 확장 가능
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }, on_conflict="store_id,session_id,category").execute()
        
        # 5. health_check_sessions 업데이트 (판독 결과 포함)
        import json
        update_data = {
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "overall_score": results['overall_score'],
            "overall_grade": results['overall_grade'],
            "main_bottleneck": results['main_bottleneck']
        }
        
        # 판독 결과를 JSON으로 저장 (diagnosis_json 컬럼이 있으면 사용, 없으면 무시)
        try:
            # JSON 필드로 저장 시도
            update_data["diagnosis_json"] = json.dumps(diagnosis, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"diagnosis_json 저장 실패 (컬럼이 없을 수 있음): {e}")
        
        supabase.table("health_check_sessions").update(update_data).eq("id", session_id).execute()
        
        logger.info(f"finalize_health_session: Session finalized - {session_id}, score: {results['overall_score']}, grade: {results['overall_grade']}")
        return True
    
    except Exception as e:
        logger.error(f"finalize_health_session: Error - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_health_session(session_id: str) -> Optional[Dict]:
    """
    건강검진 세션 조회
    
    Args:
        session_id: 세션 ID
    
    Returns:
        세션 정보 dict 또는 None
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        result = supabase.table("health_check_sessions").select("*").eq("id", session_id).execute()
        
        if result.data and len(result.data) > 0:
            from src.ui_helpers import safe_resp_first_data
            return safe_resp_first_data(result)
        return None
    
    except Exception as e:
        logger.error(f"get_health_session: Error - {e}")
        return None


def get_health_answers(session_id: str) -> List[Dict]:
    """
    건강검진 답변 조회
    
    Args:
        session_id: 세션 ID
    
    Returns:
        답변 리스트
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        result = supabase.table("health_check_answers").select("*").eq("session_id", session_id).execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        logger.error(f"get_health_answers: Error - {e}")
        return []


def get_health_diagnosis(session_id: str) -> Optional[Dict]:
    """
    건강검진 판독 결과 조회
    
    Args:
        session_id: 세션 ID
    
    Returns:
        판독 결과 dict 또는 None
        {
            "risk_axes": [...],
            "primary_pattern": {...},
            "insight_summary": [...],
            "strategy_bias": {...}
        }
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.error("get_health_diagnosis: Supabase client not available")
            return None
        
        result = supabase.table("health_check_sessions").select("diagnosis_json").eq("id", session_id).execute()
        
        from src.ui_helpers import safe_resp_first_data
        result_data = safe_resp_first_data(result)
        if not result_data or not result_data.get("diagnosis_json"):
            logger.debug(f"get_health_diagnosis: No diagnosis found for session {session_id}")
            return None
        
        import json
        diagnosis = result_data.get("diagnosis_json")
        
        # JSONB가 dict로 반환되는 경우와 문자열인 경우 모두 처리
        if isinstance(diagnosis, str):
            return json.loads(diagnosis)
        else:
            return diagnosis
    
    except Exception as e:
        logger.error(f"get_health_diagnosis: Error - {e}")
        return None


def get_health_results(session_id: str) -> List[Dict]:
    """
    건강검진 결과 조회
    
    Args:
        session_id: 세션 ID
    
    Returns:
        결과 리스트 (카테고리별)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        result = supabase.table("health_check_results").select("*").eq("session_id", session_id).execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        logger.error(f"get_health_results: Error - {e}")
        return []


def load_latest_open_session(store_id: str) -> Optional[Dict]:
    """
    최근 미완료 세션 조회
    
    Args:
        store_id: 매장 ID
    
    Returns:
        세션 정보 dict 또는 None
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        # NULL 체크: completed_at이 NULL인 세션 조회
        result = supabase.table("health_check_sessions").select("*").eq(
            "store_id", store_id
        ).is_("completed_at", "null").order("started_at", desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            from src.ui_helpers import safe_resp_first_data
            return safe_resp_first_data(result)
        return None
    
    except Exception as e:
        logger.error(f"load_latest_open_session: Error - {e}")
        return None


def list_health_sessions(store_id: str, limit: int = 10) -> List[Dict]:
    """
    건강검진 세션 목록 조회 (최근 완료된 세션)
    
    Args:
        store_id: 매장 ID
        limit: 조회할 최대 개수
    
    Returns:
        세션 리스트
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        result = supabase.table("health_check_sessions").select("*").eq(
            "store_id", store_id
        ).not_.is_("completed_at", "null").order("completed_at", desc=True).limit(limit).execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        logger.error(f"list_health_sessions: Error - {e}")
        return []
