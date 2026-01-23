# PHASE 10 / STEP 10-4: 설계 데이터 DB화 가이드

## 목적
session_state로만 저장되던 설계 데이터를 Supabase DB에 영구 저장(SSOT)하고, 설계실/가게 설계 센터/홈 판결 로직이 DB를 읽도록 전환합니다.

## 생성된 테이블
1. **menu_portfolio_state**: 메뉴별 역할 태그(미끼/볼륨/마진) SSOT
2. **ingredient_structure_state**: 재료별 설계 상태(대체 가능/발주유형/메모) SSOT
3. **design_routine_log**: 설계 루틴 체크(주간/월간 완료 기록) SSOT

---

## STEP 1: SQL 실행

### 1.1 Supabase SQL Editor 접속
1. Supabase Dashboard → SQL Editor 이동
2. 새 쿼리 작성

### 1.2 SQL 파일 실행
`sql/design_lab_state_tables.sql` 파일의 전체 내용을 복사하여 SQL Editor에 붙여넣고 실행합니다.

**예상 실행 시간**: 1~2초

**성공 메시지**:
```
PHASE 10 / STEP 10-4: 설계 데이터 DB화 테이블 생성 완료
생성된 테이블:
  1. menu_portfolio_state (메뉴 역할 태그)
  2. ingredient_structure_state (재료 설계 상태)
  3. design_routine_log (설계 루틴 로그)
RLS 정책 및 트리거가 모두 설정되었습니다.
```

---

## STEP 2: RLS 테스트

### 2.1 테이블 존재 확인
```sql
-- 테이블 존재 확인
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('menu_portfolio_state', 'ingredient_structure_state', 'design_routine_log');
```

**기대 결과**: 3개 테이블 모두 조회됨

### 2.2 RLS 활성화 확인
```sql
-- RLS 활성화 여부 확인
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('menu_portfolio_state', 'ingredient_structure_state', 'design_routine_log');
```

**기대 결과**: `rowsecurity = true` (3개 모두)

### 2.3 SELECT 테스트 (로그인 유저 기준)
```sql
-- 자신의 매장 데이터 조회 (0건이어도 에러 없으면 성공)
SELECT * FROM menu_portfolio_state LIMIT 5;
SELECT * FROM ingredient_structure_state LIMIT 5;
SELECT * FROM design_routine_log LIMIT 5;
```

**기대 결과**: 에러 없이 조회됨 (데이터가 없으면 빈 결과)

### 2.4 INSERT/UPSERT 테스트 (선택)
```sql
-- 테스트용 INSERT (실제 menu_id, ingredient_id 필요)
-- 주의: 실제 데이터가 있으면 실행하지 마세요
-- INSERT INTO menu_portfolio_state (store_id, menu_id, role_tag)
-- VALUES ((SELECT id FROM stores LIMIT 1), (SELECT id FROM menu_master LIMIT 1), '미끼');
```

---

## STEP 3: 앱 재시작 및 확인

### 3.1 앱 재시작
Streamlit 앱을 재시작합니다.

### 3.2 체크리스트

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

#### ✅ 가게 설계 센터
1. 가게 설계 센터 페이지 접속
2. **확인**: 
   - 메뉴 포트폴리오 상태 카드에 DB 기반 역할 분포가 반영되는지
   - 재료 구조 상태 카드에 DB 기반 대체/발주 구조가 반영되는지

---

## STEP 4: 에러 처리 확인

### 4.1 DB 저장 실패 시 폴백
- DB 저장 실패 시 session_state로 폴백되어야 함
- 사용자에게 경고 메시지가 표시되어야 함 (DEV 모드에서만 상세)

### 4.2 store_id가 None인 경우
- DB 저장 호출이 금지되어야 함
- 안내 메시지가 표시되어야 함

---

## 문제 해결

### 문제 1: RLS 정책 오류
**증상**: "permission denied" 또는 "row-level security policy violation"

**해결**:
1. `get_user_store_id()` 함수가 정상 작동하는지 확인
2. 사용자가 올바른 store_id에 연결되어 있는지 확인
3. SQL Editor에서 RLS 정책 재생성

### 문제 2: 트리거 오류
**증상**: "trigger function does not exist"

**해결**:
1. 트리거 함수가 생성되었는지 확인:
   ```sql
   SELECT proname FROM pg_proc WHERE proname LIKE '%menu_portfolio_state%';
   ```
2. 필요시 SQL 파일의 트리거 부분만 재실행

### 문제 3: 데이터가 저장되지 않음
**증상**: UI에서 변경했는데 새로고침 후 사라짐

**해결**:
1. 브라우저 개발자 도구 콘솔에서 에러 확인
2. Python 로그에서 DB 저장 실패 메시지 확인
3. `storage_supabase.py`의 upsert 함수가 정상 호출되는지 확인

---

## 다음 단계

SQL 실행 및 테스트 완료 후:
1. ✅ 앱 재시작
2. ✅ 메뉴 포트폴리오 설계실에서 역할 태그 저장 확인
3. ✅ 재료 구조 설계실에서 toggle/selectbox 저장 확인
4. ✅ 가게 설계 센터에서 DB 기반 점수 반영 확인

모든 체크리스트가 완료되면 PHASE 10 / STEP 10-4 작업이 완료된 것입니다.
