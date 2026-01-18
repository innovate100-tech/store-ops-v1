# Store Ops v1 - Supabase 설정 가이드

이 가이드는 Store Ops v1을 Supabase(Postgres + Auth)로 업그레이드하는 방법을 단계별로 설명합니다.

## 📋 목차

1. [Supabase 프로젝트 생성](#1-supabase-프로젝트-생성)
2. [데이터베이스 스키마 생성](#2-데이터베이스-스키마-생성)
3. [인증 설정](#3-인증-설정)
4. [Streamlit Secrets 설정](#4-streamlit-secrets-설정)
5. [CSV 데이터 마이그레이션](#5-csv-데이터-마이그레이션)
6. [사용자 계정 생성](#6-사용자-계정-생성)
7. [앱 실행](#7-앱-실행)

---

## 1. Supabase 프로젝트 생성

1. [Supabase](https://supabase.com)에 가입하고 로그인
2. "New Project" 클릭
3. 프로젝트 정보 입력:
   - **Name**: store-ops-v1 (또는 원하는 이름)
   - **Database Password**: 강한 비밀번호 입력 (기억해두세요!)
   - **Region**: 가장 가까운 리전 선택
4. "Create new project" 클릭 (1-2분 소요)

---

## 2. 데이터베이스 스키마 생성

1. Supabase 대시보드에서 왼쪽 메뉴의 **SQL Editor** 클릭
2. "New query" 클릭
3. `sql/schema.sql` 파일의 전체 내용을 복사하여 붙여넣기
4. "Run" 버튼 클릭 (또는 Ctrl+Enter)
5. 성공 메시지 확인

**확인 사항:**
- 모든 테이블이 생성되었는지 확인: `Table Editor` 메뉴에서 테이블 목록 확인
- RLS가 활성화되었는지 확인: 각 테이블의 "Policies" 탭에서 RLS가 ON인지 확인

---

## 3. 인증 설정

1. Supabase 대시보드에서 **Authentication** > **Providers** 클릭
2. **Email** 프로바이더가 활성화되어 있는지 확인
3. 필요시 **Settings** > **Auth**에서 다음 설정 확인:
   - "Enable Email Signup": ON
   - "Confirm email": OFF (개발 환경) 또는 ON (프로덕션)

---

## 4. Streamlit Secrets 설정

### 로컬 개발 환경

1. `.streamlit` 디렉토리 생성 (없으면)
   ```bash
   mkdir .streamlit
   ```

2. `.streamlit/secrets.toml.example` 파일을 복사하여 `.streamlit/secrets.toml` 생성
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

3. `.streamlit/secrets.toml` 파일 편집:
   ```toml
   [supabase]
   url = "https://your-project-id.supabase.co"
   anon_key = "your-anon-key-here"
   ```
   
   ⚠️ **중요**: `service_role_key`는 절대 넣지 마세요! 앱은 `anon_key`만 사용합니다.

4. Supabase 대시보드에서 API 키 확인:
   - **Settings** > **API** 메뉴
   - **Project URL**: `url` 값 복사
   - **anon public key**: `anon_key` 값 복사

### Streamlit Cloud 배포

1. [Streamlit Cloud](https://streamlit.io/cloud)에 접속
2. 앱 선택 또는 새 앱 생성
3. **Settings** > **Secrets** 메뉴
4. 다음 내용을 입력:
   ```toml
   [supabase]
   url = "https://your-project-id.supabase.co"
   anon_key = "your-anon-key-here"
   ```
   
   ⚠️ **중요**: `service_role_key`는 절대 넣지 마세요!
5. **Save** 클릭

---

## 5. CSV 데이터 마이그레이션

기존 CSV 데이터를 Supabase로 옮기기:

1. Python 환경 활성화 및 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```

2. 마이그레이션 스크립트 실행:
   ```bash
   python scripts/migrate_csv_to_db.py
   ```

**주의:**
- 이 스크립트는 `service_role_key`를 사용하여 RLS를 우회합니다
- 기본 매장명은 "Plate&Share"입니다. 다른 이름을 사용하려면 스크립트 수정 필요

**확인:**
- Supabase 대시보드 > **Table Editor**에서 데이터가 제대로 들어갔는지 확인

---

## 6. 첫 매장 및 점장 계정 생성 (초보자용)

### 단계별 가이드

#### 1단계: 매장 생성 SQL 실행

Supabase 대시보드 > **SQL Editor**에서 다음 SQL 실행:

```sql
-- 매장 생성
INSERT INTO stores (name)
VALUES ('Plate&Share')
RETURNING id, name;
```

**중요**: 실행 결과에서 **매장 ID (UUID)**를 복사해두세요!

#### 2단계: Supabase Auth에서 사용자 생성

1. Supabase 대시보드 > **Authentication** > **Users** 메뉴
2. "Add user" > "Create new user" 클릭
3. 정보 입력:
   - **Email**: 점장 이메일 (예: manager@example.com)
   - **Password**: 비밀번호 (점장이 로그인에 사용)
   - **Auto Confirm User**: ✅ 체크 (이메일 인증 스킵)
4. "Create user" 클릭
5. 생성된 사용자의 **ID (UUID)**를 복사해두세요!

#### 3단계: user_profiles 테이블에 프로필 등록

SQL Editor에서 다음 SQL 실행 (ID는 위에서 복사한 값으로 교체):

```sql
-- user_profiles에 등록
INSERT INTO user_profiles (id, store_id, role)
VALUES (
    'USER_ID_HERE',    -- 2단계에서 복사한 사용자 ID
    'STORE_ID_HERE',   -- 1단계에서 복사한 매장 ID
    'manager'
);
```

#### 4단계: 확인

다음 SQL로 확인:

```sql
-- 생성 결과 확인
SELECT 
    up.id as user_id,
    au.email,
    up.store_id,
    s.name as store_name,
    up.role
FROM user_profiles up
JOIN auth.users au ON up.id = au.id
LEFT JOIN stores s ON up.store_id = s.id;
```

정상적으로 등록되었다면 사용자 정보가 표시됩니다.

### 도우미 스크립트 사용 (선택사항)

더 쉽게 하려면 스크립트를 사용할 수 있습니다:

```bash
python scripts/bootstrap_store_and_manager.py
```

이 스크립트는 SQL 파일(`scripts/bootstrap.sql`)을 생성합니다. 
Supabase SQL Editor에서 해당 파일의 SQL을 실행하면 됩니다.

### 매장 ID 확인 방법

1. Supabase 대시보드 > **Table Editor** > **stores** 테이블
2. 매장의 `id` (UUID) 확인

---

## 7. 앱 실행

1. Streamlit 앱 실행:
   ```bash
   streamlit run app.py
   ```

2. 브라우저에서 앱 열기
3. 로그인 화면에서 이메일/비밀번호 입력
4. 로그인 성공 시 자신의 매장 데이터만 보이도록 됩니다

---

## 🔒 보안 주의사항

1. **service_role_key**는 절대 클라이언트 코드나 공개 저장소에 올리지 마세요
2. **anon_key**는 공개되어도 RLS로 보호되지만, 최소 권한 원칙을 따르세요
3. Supabase 대시보드에서 **Settings** > **API** > **RLS**가 활성화되어 있는지 확인

---

## 🐛 문제 해결

### "Supabase not available" 오류

- `.streamlit/secrets.toml` 파일이 올바른 위치에 있는지 확인
- Secrets의 `url`과 `anon_key` 값이 올바른지 확인

### "No store_id found" 오류

- 사용자가 `users` 테이블에 등록되어 있는지 확인
- `users` 테이블의 `store_id`가 올바른지 확인

### RLS 오류

- SQL Editor에서 RLS 정책이 제대로 생성되었는지 확인:
  ```sql
  SELECT * FROM pg_policies WHERE tablename = 'sales';
  ```

### 마이그레이션 실패

- `service_role_key`가 올바른지 확인
- CSV 파일 경로가 올바른지 확인 (`data/` 디렉토리)

---

## 📚 추가 리소스

- [Supabase 문서](https://supabase.com/docs)
- [Streamlit Secrets 관리](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [Row Level Security 가이드](https://supabase.com/docs/guides/auth/row-level-security)
