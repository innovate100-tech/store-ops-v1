"""
첫 매장과 점장 계정을 생성하는 스크립트

사용법:
    python scripts/bootstrap_store_and_manager.py

이 스크립트는:
1. 매장 1개 생성
2. 지정한 user_id를 그 매장의 manager로 user_profiles에 연결

주의: service_role_key는 사용하지 않고, 수동으로 SQL을 실행하도록 안내합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_bootstrap_sql(store_name: str = "Plate&Share", user_email: str = "") -> str:
    """
    부트스트랩 SQL 생성
    
    Args:
        store_name: 매장명
        user_email: 사용자 이메일 (선택사항, 확인용)
    
    Returns:
        str: SQL 스크립트
    """
    sql = f"""
-- ============================================
-- 매장 및 점장 계정 부트스트랩
-- ============================================
-- 이 SQL은 Supabase SQL Editor에서 직접 실행하세요.

-- 1. 매장 생성
INSERT INTO stores (name)
VALUES ('{store_name}')
ON CONFLICT DO NOTHING
RETURNING id, name;

-- 2. 생성된 매장 ID 확인 (위 쿼리 결과에서 복사)
-- 예: '123e4567-e89b-12d3-a456-426614174000'

-- 3. Supabase Auth에서 사용자 생성 (대시보드에서 수동)
-- Authentication > Users > Add user
-- 이메일: {user_email if user_email else "your-email@example.com"}
-- 비밀번호: (원하는 비밀번호)
-- 사용자 생성 후 ID 복사 (예: 'abc12345-...')

-- 4. user_profiles에 프로필 등록
-- 아래 쿼리에서 매장 ID와 사용자 ID를 실제 값으로 교체하세요:

/*
INSERT INTO user_profiles (id, store_id, role)
VALUES (
    'USER_ID_HERE',  -- Supabase Auth에서 생성한 사용자의 ID
    'STORE_ID_HERE',  -- 위 1번에서 생성한 매장의 ID
    'manager'
);
*/

-- ============================================
-- 확인 쿼리
-- ============================================
-- 매장 목록 확인
SELECT id, name, created_at FROM stores;

-- 사용자 프로필 확인
SELECT 
    up.id as user_id,
    au.email,
    up.store_id,
    s.name as store_name,
    up.role
FROM user_profiles up
JOIN auth.users au ON up.id = au.id
LEFT JOIN stores s ON up.store_id = s.id;
"""
    return sql


def main():
    """메인 함수"""
    print("=" * 70)
    print("매장 및 점장 계정 부트스트랩 가이드")
    print("=" * 70)
    print()
    
    # 매장명 입력
    store_name = input("매장명을 입력하세요 (기본: Plate&Share): ").strip()
    if not store_name:
        store_name = "Plate&Share"
    
    # 이메일 입력
    user_email = input("점장 이메일을 입력하세요 (선택사항): ").strip()
    
    # SQL 생성
    sql = generate_bootstrap_sql(store_name, user_email)
    
    # SQL 파일로 저장
    sql_file = project_root / "scripts" / "bootstrap.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(sql)
    
    print(f"\n✓ SQL 스크립트가 생성되었습니다: {sql_file}")
    print()
    print("=" * 70)
    print("다음 단계:")
    print("=" * 70)
    print()
    print("1. Supabase 대시보드 > SQL Editor 열기")
    print("2. 아래 SQL 파일을 열어서 확인:")
    print(f"   {sql_file}")
    print()
    print("3. 순서대로 실행:")
    print("   - 매장 생성 쿼리 실행 → 매장 ID 복사")
    print("   - Supabase Auth에서 사용자 생성 → 사용자 ID 복사")
    print("   - user_profiles INSERT 쿼리에서 ID 교체 후 실행")
    print()
    print("4. 확인 쿼리로 결과 확인")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
