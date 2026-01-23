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
from src.health_check.questions_bank import CATEGORIES, get_question_code

logger = logging.getLogger(__name__)


def create_health_session(store_id: str, check_type: str = 'ad-hoc') -> Optional[str]:
    """
    건강검진 세션 생성
    
    Args:
        store_id: 매장 ID
        check_type: 검진 유형 ('ad-hoc' | 'regular' | 'periodic')
    
    Returns:
        session_id (UUID) 또는 None (실패 시)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.error("create_health_session: Supabase client not available")
            return None
        
        result = supabase.table("health_check_sessions").insert({
            "store_id": store_id,
            "check_type": check_type,
            "started_at": datetime.utcnow().isoformat() + "Z"
        }).execute()
        
        if result.data and len(result.data) > 0:
            session_id = result.data[0]['id']
            logger.info(f"create_health_session: Session created - {session_id}")
            return session_id
        else:
            logger.error("create_health_session: No data returned from insert")
            return None
    
    except Exception as e:
        logger.error(f"create_health_session: Error - {e}")
        return None


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
        
        # 5. health_check_sessions 업데이트
        supabase.table("health_check_sessions").update({
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "overall_score": results['overall_score'],
            "overall_grade": results['overall_grade'],
            "main_bottleneck": results['main_bottleneck']
        }).eq("id", session_id).execute()
        
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
            return result.data[0]
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
