"""
건강검진 판독 엔진 DEV 테스트 스크립트

최근 완료 검진 1건 로드 → 판독 실행 → 결과 출력
"""

import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.health_check.storage import (
    get_health_session,
    get_health_results,
    get_health_diagnosis
)
from src.health_check.health_diagnosis_engine import diagnose_health_check
from src.auth import get_current_store_id, get_supabase_client
import streamlit as st

# Streamlit 없이 실행 가능하도록 수정
def test_diagnosis_from_latest_session():
    """최근 완료 검진 1건 로드 → 판독 실행"""
    print("=" * 60)
    print("건강검진 판독 엔진 DEV 테스트 (최근 검진)")
    print("=" * 60)
    
    try:
        # store_id 가져오기
        store_id = get_current_store_id()
        if not store_id:
            print("❌ store_id를 찾을 수 없습니다.")
            return
        
        print(f"✅ store_id: {store_id}")
        
        # Supabase 클라이언트로 최근 완료 검진 조회
        supabase = get_supabase_client()
        if not supabase:
            print("❌ Supabase 클라이언트를 생성할 수 없습니다.")
            return
        
        # 최근 완료 검진 1건 조회
        result = supabase.table("health_check_sessions").select(
            "id, completed_at, overall_score, overall_grade, diagnosis_json"
        ).eq("store_id", store_id).not_.is_("completed_at", "null").order(
            "completed_at", desc=True
        ).limit(1).execute()
        
        if not result.data:
            print("❌ 완료된 검진이 없습니다.")
            return
        
        session = result.data[0]
        session_id = session["id"]
        print(f"\n✅ 최근 완료 검진 발견:")
        print(f"   - session_id: {session_id}")
        print(f"   - 완료일시: {session.get('completed_at')}")
        print(f"   - 전체 점수: {session.get('overall_score')}")
        print(f"   - 등급: {session.get('overall_grade')}")
        
        # 검진 결과 로드
        results = get_health_results(session_id)
        if not results:
            print("❌ 검진 결과를 찾을 수 없습니다.")
            return
        
        # axis_scores 구성
        axis_scores = {}
        for r in results:
            category = r.get("category")
            score_avg = r.get("score_avg")
            if category and score_avg is not None:
                axis_scores[category] = float(score_avg)
        
        print(f"\n✅ 축별 점수:")
        for axis, score in sorted(axis_scores.items()):
            print(f"   - {axis}: {score:.1f}")
        
        # 판독 실행
        print(f"\n🔍 판독 엔진 실행 중...")
        diagnosis = diagnose_health_check(
            session_id=session_id,
            store_id=store_id,
            axis_scores=axis_scores,
            axis_raw=None,
            meta=None
        )
        
        # 결과 출력
        print(f"\n" + "=" * 60)
        print("판독 결과")
        print("=" * 60)
        
        print(f"\n📊 패턴:")
        pattern = diagnosis.get("primary_pattern", {})
        print(f"   - 코드: {pattern.get('code')}")
        print(f"   - 제목: {pattern.get('title')}")
        print(f"   - 설명: {pattern.get('description')}")
        
        print(f"\n⚠️ Top3 리스크:")
        for i, risk in enumerate(diagnosis.get("risk_axes", [])[:3], 1):
            print(f"   {i}. {risk['axis']} 축: {risk['score']}/10 ({risk['level']})")
            print(f"      → {risk['reason']}")
        
        print(f"\n💡 판독 요약:")
        for i, insight in enumerate(diagnosis.get("insight_summary", []), 1):
            print(f"   {i}. {insight}")
        
        print(f"\n🎯 전략 가중치:")
        for strategy, weight in diagnosis.get("strategy_bias", {}).items():
            print(f"   - {strategy}: {weight:.2f}")
        
        print(f"\n" + "=" * 60)
        print("✅ 판독 테스트 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Streamlit 없이 실행
    test_diagnosis_from_latest_session()
