# Phase 8-A Step 1-A: DB 스키마 변경 영향 범위 분석

## 📋 실행 전 확인사항

### SQL 파일 위치
- `sql/phase8a_step1.sql`

### 실행 방법
1. Supabase 대시보드 > SQL Editor 열기
2. `sql/phase8a_step1.sql` 파일 내용 복사
3. SQL Editor에 붙여넣기
4. **실행 전 반드시 영향 범위 확인**
5. 실행 후 검증 쿼리 실행 (Step 1-B에서 제공)

---

## 🔍 영향 범위 요약

### 1. 기존 테이블/컬럼 변경

#### ✅ 안전한 변경 (기존 데이터 보존)

| 테이블 | 변경 내용 | 영향 | 다운타임 |
|--------|----------|------|----------|
| `stores` | `created_by` 컬럼 추가 (NULL 허용) | ✅ 없음 | ❌ 없음 |
| `user_profiles` | `default_store_id` 컬럼 추가 (NULL 허용) | ✅ 없음 | ❌ 없음 |
| `user_profiles` | `onboarding_mode` 컬럼 추가 (기본값 'coach') | ✅ 없음 | ❌ 없음 |

**설명:**
- 모든 컬럼 추가는 `IF NOT EXISTS` 체크로 중복 실행 안전
- NULL 허용이므로 기존 데이터에 영향 없음
- 기존 컬럼 삭제 없음 (파괴적 변경 없음)

#### ✅ 신규 테이블 생성

| 테이블 | 목적 | 기존 데이터 영향 |
|--------|------|-----------------|
| `store_members` | 사용자-매장 멤버십 (다중 매장 지원) | ✅ 없음 (신규 테이블) |

**설명:**
- 완전히 새로운 테이블이므로 기존 데이터에 영향 없음
- `CREATE TABLE IF NOT EXISTS`로 중복 실행 안전

---

### 2. 기존 데이터가 깨질 가능성

#### ✅ 안전 (데이터 손실 없음)

1. **stores 테이블:**
   - `created_by` 컬럼 추가만 수행
   - 기존 row의 `created_by`는 NULL로 유지
   - 기존 데이터 변경 없음

2. **user_profiles 테이블:**
   - `default_store_id`, `onboarding_mode` 컬럼 추가만 수행
   - 기존 `store_id` 컬럼은 **유지** (호환성)
   - 기존 row는 자동으로 `default_store_id = store_id`로 설정됨
   - 기존 데이터 변경 없음

3. **store_members 테이블:**
   - 신규 테이블이므로 기존 데이터 없음
   - 마이그레이션 스크립트가 기존 `user_profiles.store_id`를 자동으로 `store_members`에 복사
   - 기존 데이터 보존됨

#### ⚠️ 주의사항

- **기존 `user_profiles.store_id` 컬럼은 삭제하지 않음**
  - 레거시 호환을 위해 유지
  - 점진적 전환 계획:
    1. Step 1: `default_store_id` 추가 + `store_members` 생성
    2. Step 4-7: 코드에서 `default_store_id` 우선 사용
    3. 이후: `store_id` 컬럼은 deprecated로 표시 (삭제는 나중에)

---

### 3. 다운타임/롤백 포인트

#### 다운타임
- ❌ **다운타임 없음**
  - 컬럼 추가는 ALTER TABLE로 즉시 완료
  - 테이블 생성도 즉시 완료
  - 기존 쿼리는 영향 없음

#### 롤백 포인트

**롤백 방법 1: 컬럼 삭제 (필요시)**
```sql
-- stores 테이블 롤백
ALTER TABLE stores DROP COLUMN IF EXISTS created_by;

-- user_profiles 테이블 롤백
ALTER TABLE user_profiles DROP COLUMN IF EXISTS default_store_id;
ALTER TABLE user_profiles DROP COLUMN IF EXISTS onboarding_mode;
```

**롤백 방법 2: 테이블 삭제 (필요시)**
```sql
-- store_members 테이블 삭제
DROP TABLE IF EXISTS store_members CASCADE;
```

**롤백 방법 3: 함수 롤백**
```sql
-- Helper 함수들을 이전 버전으로 복원
-- (기존 schema.sql의 get_user_store_id() 함수로 복원)
```

**⚠️ 주의:**
- 롤백 시 마이그레이션된 `store_members` 데이터는 삭제됨
- 하지만 원본 `user_profiles.store_id`는 유지되므로 데이터 손실 없음

---

## 📊 변경 사항 상세

### 1. stores 테이블
```sql
-- 추가되는 컬럼
created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
```
- **목적**: 매장 생성자 추적
- **기존 데이터**: `created_by = NULL`로 유지
- **인덱스**: `idx_stores_created_by` 자동 생성

### 2. store_members 테이블 (신규)
```sql
CREATE TABLE store_members (
    id UUID PRIMARY KEY,
    store_id UUID NOT NULL REFERENCES stores(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    role TEXT NOT NULL CHECK (role IN ('owner', 'manager', 'staff')),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    UNIQUE(store_id, user_id)
);
```
- **목적**: 다중 매장 멤버십 지원
- **기존 데이터**: 없음 (신규)
- **마이그레이션**: `user_profiles.store_id` → `store_members` 자동 복사

### 3. user_profiles 테이블
```sql
-- 추가되는 컬럼
default_store_id UUID REFERENCES stores(id) ON DELETE SET NULL
onboarding_mode TEXT NOT NULL DEFAULT 'coach' CHECK (onboarding_mode IN ('coach', 'fast'))
```
- **목적**: 
  - `default_store_id`: 선호 매장 (매장 선택 시 기본값)
  - `onboarding_mode`: 온보딩 모드 설정
- **기존 데이터**: 
  - `default_store_id`는 자동으로 `store_id` 값으로 설정됨
  - `onboarding_mode`는 기본값 'coach'로 설정됨
- **레거시 호환**: `store_id` 컬럼은 유지 (삭제 안 함)

### 4. Helper 함수 업데이트

#### `get_user_store_id()` 함수 업데이트
- **이전**: `user_profiles.store_id`만 조회
- **이후**: 
  1. `store_members`에서 첫 번째 매장 (owner 우선)
  2. `user_profiles.default_store_id`
  3. `user_profiles.store_id` (레거시 호환)

#### 신규 함수
- `get_user_store_ids()`: 사용자의 모든 매장 목록 반환
- `is_user_store_member(check_store_id)`: 특정 매장 멤버십 확인

---

## ✅ 검증 체크리스트 (Step 1-B에서 실행)

### 실행 전 확인
- [ ] Supabase 대시보드 접근 가능
- [ ] SQL Editor 열림
- [ ] 백업 필요 시 백업 완료

### 실행 후 확인
- [ ] `stores` 테이블에 `created_by` 컬럼 존재
- [ ] `store_members` 테이블 생성됨
- [ ] `user_profiles` 테이블에 `default_store_id`, `onboarding_mode` 컬럼 존재
- [ ] Helper 함수들이 정상 생성됨
- [ ] 기존 데이터가 정상적으로 마이그레이션됨

---

## 🚨 주의사항

### 절대 하지 말 것
- ❌ DROP TABLE (기존 테이블 삭제)
- ❌ TRUNCATE (기존 데이터 삭제)
- ❌ ALTER TABLE ... DROP COLUMN (기존 컬럼 삭제)
- ❌ NOT NULL 제약 추가 (기존 NULL 데이터와 충돌)

### 안전하게 실행되는 것
- ✅ ALTER TABLE ... ADD COLUMN (NULL 허용)
- ✅ CREATE TABLE IF NOT EXISTS
- ✅ CREATE INDEX IF NOT EXISTS
- ✅ CREATE OR REPLACE FUNCTION

---

## 📝 다음 단계 (Step 1-B)

Step 1-A SQL 실행 후:
1. 검증 쿼리 실행
2. 각 테이블 구조 확인
3. 데이터 마이그레이션 결과 확인
4. Helper 함수 동작 확인

---

## 🔄 점진적 전환 계획

### Phase 1 (현재 Step 1)
- `store_members` 테이블 생성
- `default_store_id` 추가
- 기존 `store_id` 유지 (호환성)

### Phase 2 (Step 4-7)
- 코드에서 `default_store_id` 우선 사용
- `store_members` 기반 매장 선택 구현
- `user_profiles.store_id`는 fallback으로만 사용

### Phase 3 (향후)
- 모든 코드가 `store_members` 기반으로 전환 완료
- `user_profiles.store_id` deprecated 표시
- (선택) `user_profiles.store_id` 컬럼 삭제 (충분한 검증 후)

---

## 📌 요약

| 항목 | 상태 | 설명 |
|------|------|------|
| **기존 데이터 손실** | ✅ 없음 | 모든 변경은 추가만 수행 |
| **다운타임** | ❌ 없음 | ALTER TABLE은 즉시 완료 |
| **롤백 가능** | ✅ 가능 | 컬럼/테이블 삭제로 롤백 |
| **호환성** | ✅ 유지 | 기존 `store_id` 컬럼 유지 |
| **안전성** | ✅ 높음 | IF NOT EXISTS 체크로 중복 실행 안전 |

**결론: 안전하게 실행 가능합니다. ✅**
