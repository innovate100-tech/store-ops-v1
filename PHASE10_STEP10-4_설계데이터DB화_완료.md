# PHASE 10 / STEP 10-4: 설계 데이터 DB화 완료

## 작업 개요
session_state로만 저장되던 설계 데이터를 Supabase DB에 영구 저장(SSOT)하고, 설계실/가게 설계 센터/홈 판결 로직이 DB를 읽도록 전환 완료.

---

## 생성/수정된 파일 목록

### 1. SQL 파일
- **`sql/design_lab_state_tables.sql`** (신규)
  - `menu_portfolio_state` 테이블 생성
  - `ingredient_structure_state` 테이블 생성
  - `design_routine_log` 테이블 생성
  - RLS 정책 설정
  - updated_by/updated_at 자동화 트리거

### 2. 가이드 문서
- **`docs/PHASE10_STEP10-4_DB화_가이드.md`** (신규)
  - SQL 실행 가이드
  - RLS 테스트 쿼리
  - 앱 재시작 및 확인 체크리스트

### 3. Storage 함수 추가
- **`src/storage_supabase.py`** (수정)
  - `load_menu_role_tags(store_id)` - 메뉴 역할 태그 조회
  - `upsert_menu_role_tag(store_id, menu_id, role_tag)` - 메뉴 역할 태그 저장
  - `load_ingredient_structure_state(store_id)` - 재료 설계 상태 조회
  - `upsert_ingredient_structure_state(...)` - 재료 설계 상태 저장
  - `upsert_design_routine_log(...)` - 설계 루틴 로그 저장
  - `load_design_routine_logs(...)` - 설계 루틴 로그 조회

### 4. Helper 함수 수정
- **`ui_pages/design_lab/menu_portfolio_helpers.py`** (수정)
  - `get_menu_portfolio_tags()` - DB 우선 로드, session_state 폴백
  - `set_menu_portfolio_tag()` - DB 저장 우선, 실패 시 session_state 폴백
  - `_get_menu_id_map()` - 메뉴명 -> menu_id 매핑 헬퍼 추가

### 5. UI 연결
- **`ui_pages/menu_management.py`** (수정 불필요)
  - 기존 `set_menu_portfolio_tag()` 호출이 DB 우선으로 자동 전환됨

- **`ui_pages/ingredient_management.py`** (수정)
  - `_render_ingredient_strategy_tools()` 함수 수정
  - DB에서 재료 설계 상태 초기값 로드
  - toggle/selectbox 변경 시 즉시 DB upsert
  - 메모 저장 버튼 추가 (substitute_memo, strategy_memo)

### 6. Design Center 반영
- **`ui_pages/design_lab/design_center_data.py`** (수정 불필요)
  - 기존 `get_menu_portfolio_tags()` 호출이 DB 우선으로 자동 전환됨

---

## 핵심 구현 내용

### 1. 테이블 구조

#### menu_portfolio_state
- `store_id`, `menu_id` (UNIQUE)
- `role_tag` ('미끼', '볼륨', '마진')
- `updated_by`, `updated_at` (자동)

#### ingredient_structure_state
- `store_id`, `ingredient_id` (UNIQUE)
- `is_substitutable` (boolean)
- `order_type` ('single', 'multi', 'unset')
- `substitute_memo`, `strategy_memo` (text)
- `updated_by`, `updated_at` (자동)

#### design_routine_log
- `store_id`, `routine_type`, `period_key` (UNIQUE)
- `completed_by`, `completed_at` (자동)

### 2. RLS 정책
- 모든 테이블에 `get_user_store_id()` 기반 RLS 적용
- SELECT/INSERT/UPDATE/DELETE 정책 모두 설정

### 3. DB 우선 로직
- **메뉴 역할 태그**: DB 로드 → session_state 캐시 → DB 저장 → 실패 시 session_state 폴백
- **재료 설계 상태**: DB 로드 → UI 초기값 설정 → 변경 시 즉시 DB upsert → 실패 시 session_state 폴백

### 4. 메뉴명/재료명 -> ID 변환
- `menu_portfolio_helpers.py`: `_get_menu_id_map()` 헬퍼로 메뉴명 -> menu_id 변환
- `ingredient_management.py`: `load_csv()` 결과에서 `id` 컬럼 사용

---

## 검증 방법

### 1. SQL 실행 확인
```sql
-- 테이블 존재 확인
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('menu_portfolio_state', 'ingredient_structure_state', 'design_routine_log');

-- RLS 활성화 확인
SELECT tablename, rowsecurity FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('menu_portfolio_state', 'ingredient_structure_state', 'design_routine_log');
```

### 2. 앱에서 확인

#### ✅ 메뉴 포트폴리오 설계실
1. 메뉴 포트폴리오 설계실 페이지 접속
2. 역할 태그(미끼/볼륨/마진) 1개 변경
3. 페이지 새로고침 (F5)
4. **확인**: 변경한 역할 태그가 유지되는지 확인

#### ✅ 재료 구조 설계실
1. 재료 구조 설계실 페이지 접속
2. 고위험 재료 테이블에서:
   - 대체 가능 toggle 변경
   - 발주 유형 selectbox 변경
3. 페이지 새로고침 (F5)
4. **확인**: 변경한 값들이 유지되는지 확인
5. 대체 구조 설계 패널에서 메모 입력 후 "메모 저장" 버튼 클릭
6. **확인**: 메모가 저장되고 새로고침 후에도 유지되는지 확인

#### ✅ 가게 설계 센터
1. 가게 설계 센터 페이지 접속
2. **확인**: 
   - 메뉴 포트폴리오 상태 카드에 DB 기반 역할 분포가 반영되는지
   - 재료 구조 상태 카드에 DB 기반 대체/발주 구조가 반영되는지

---

## 안전장치

### 1. DB 저장 실패 시 폴백
- DB 저장 실패 시 자동으로 session_state에 저장
- DEV 모드에서만 상세 에러 메시지 표시

### 2. store_id 검증
- `store_id`가 None이면 DB 저장 호출 금지
- 안내 메시지 표시

### 3. menu_id/ingredient_id 변환 실패
- ID를 찾을 수 없으면 session_state만 저장
- DEV 모드에서 경고 메시지 표시

---

## 다음 단계

1. ✅ SQL 실행 (`sql/design_lab_state_tables.sql`)
2. ✅ RLS 테스트 (가이드 문서 참조)
3. ✅ 앱 재시작
4. ✅ 메뉴 포트폴리오 설계실에서 역할 태그 저장 확인
5. ✅ 재료 구조 설계실에서 toggle/selectbox/메모 저장 확인
6. ✅ 가게 설계 센터에서 DB 기반 점수 반영 확인

모든 체크리스트가 완료되면 PHASE 10 / STEP 10-4 작업이 완료된 것입니다.

---

## 주의사항

1. **SQL 실행 필수**: 앱 사용 전 반드시 `sql/design_lab_state_tables.sql`을 Supabase SQL Editor에서 실행해야 합니다.

2. **기존 session_state 데이터**: 기존 session_state에 저장된 데이터는 자동으로 DB로 마이그레이션되지 않습니다. 사용자가 UI에서 다시 설정하면 DB에 저장됩니다.

3. **메뉴/재료 삭제 시**: 메뉴나 재료가 삭제되면 해당 설계 데이터도 CASCADE로 삭제됩니다 (외래키 제약).

4. **성능**: DB 조회는 캐시를 활용하지만, 첫 로드 시 약간의 지연이 발생할 수 있습니다.

---

## 완료일
2026-01-23
