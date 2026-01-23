"""
건강검진 시스템 DEV 검증 스크립트
더미 데이터로 세션 생성 → 답변 입력 → 결과 계산 테스트
"""

import sys
import os
import random

# 프로젝트 루트를 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.health_check.storage import (
    create_health_session,
    upsert_health_answer,
    finalize_health_session,
    get_health_session,
    get_health_results
)
from src.health_check.questions_bank import CATEGORIES, QUESTIONS_BANK, get_question_code


def generate_random_answers(store_id: str, session_id: str):
    """
    임의의 답변 90개 생성 (9개 카테고리 * 10문항)
    
    Args:
        store_id: 매장 ID
        session_id: 세션 ID
    """
    raw_values = ['yes', 'maybe', 'no']
    weights = [0.4, 0.3, 0.3]  # yes가 조금 더 많이 나오도록
    
    total_answers = 0
    
    for category in CATEGORIES:
        questions = QUESTIONS_BANK.get(category, {})
        
        # QUESTIONS_BANK의 키를 직접 사용 (P1_1 형식 등 이미 올바른 형식)
        for question_code, question_text in questions.items():
            # 랜덤 답변 선택
            raw_value = random.choices(raw_values, weights=weights)[0]
            
            # 답변 저장
            success = upsert_health_answer(
                store_id=store_id,
                session_id=session_id,
                category=category,
                question_code=question_code,
                raw_value=raw_value,
                memo=None
            )
            
            if success:
                total_answers += 1
                print(f"  ✓ {category}/{question_code}: {raw_value}")
            else:
                print(f"  ✗ {category}/{question_code}: 저장 실패")
    
    print(f"\n총 {total_answers}개 답변 저장 완료")
    return total_answers


def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("건강검진 시스템 DEV 검증 스크립트")
    print("=" * 60)
    print()
    
    # store_id 입력 받기
    store_id = input("store_id를 입력하세요 (UUID): ").strip()
    
    if not store_id:
        print("❌ store_id가 필요합니다.")
        return
    
    print(f"\n📋 store_id: {store_id}")
    print()
    
    # 1. 세션 생성
    print("1️⃣  건강검진 세션 생성 중...")
    session_id = create_health_session(store_id, check_type='ad-hoc')
    
    if not session_id:
        print("❌ 세션 생성 실패")
        return
    
    print(f"✓ 세션 생성 완료: {session_id}")
    print()
    
    # 2. 임의 답변 90개 업서트
    print("2️⃣  임의 답변 생성 및 저장 중...")
    print("   (9개 카테고리 * 10문항 = 90개)")
    print()
    
    total_answers = generate_random_answers(store_id, session_id)
    print()
    
    if total_answers == 0:
        print("❌ 답변이 저장되지 않았습니다.")
        return
    
    # 3. 세션 완료 처리 (결과 계산)
    print("3️⃣  세션 완료 처리 및 결과 계산 중...")
    success = finalize_health_session(store_id, session_id)
    
    if not success:
        print("❌ 세션 완료 처리 실패")
        return
    
    print("✓ 세션 완료 처리 완료")
    print()
    
    # 4. 결과 조회 및 출력
    print("4️⃣  결과 조회 중...")
    session = get_health_session(session_id)
    results = get_health_results(session_id)
    
    if not session:
        print("❌ 세션 정보를 가져올 수 없습니다.")
        return
    
    print()
    print("=" * 60)
    print("📊 건강검진 결과")
    print("=" * 60)
    print()
    
    # 전체 점수/등급/병목
    print(f"🎯 전체 점수: {session.get('overall_score', 'N/A')}")
    print(f"📈 전체 등급: {session.get('overall_grade', 'N/A')}")
    print(f"⚠️  주요 병목: {session.get('main_bottleneck', 'N/A')}")
    print()
    
    # 카테고리별 결과
    print("📋 카테고리별 결과:")
    print("-" * 60)
    
    # 카테고리별로 정렬하여 출력
    category_names = {
        'Q': '품질(Quality)',
        'S': '서비스(Service)',
        'C': '청결(Cleanliness)',
        'P1': '가격1(Price1)',
        'P2': '가격2(Price2)',
        'P3': '가격3(Price3)',
        'M': '마케팅(Marketing)',
        'H': '인력(Human)',
        'F': '재무(Finance)'
    }
    
    risk_level_emoji = {
        'green': '🟢',
        'yellow': '🟡',
        'red': '🔴'
    }
    
    # results를 카테고리별로 딕셔너리로 변환
    results_dict = {r['category']: r for r in results}
    
    for category in CATEGORIES:
        if category in results_dict:
            result = results_dict[category]
            score = result.get('score_avg', 0)
            risk = result.get('risk_level', 'unknown')
            emoji = risk_level_emoji.get(risk, '⚪')
            
            print(f"  {emoji} {category_names.get(category, category)}: {score:.1f}점 ({risk})")
        else:
            print(f"  ⚪ {category_names.get(category, category)}: 데이터 없음")
    
    print()
    print("=" * 60)
    print("✅ 검증 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
