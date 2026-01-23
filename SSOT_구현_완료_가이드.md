# SSOT 구현 완료 가이드

## 📋 작업 완료 내역

### ✅ STEP 1: 조회용 SSOT VIEW 생성 (SQL)

**파일:** `sql/ssot_views_and_audit.sql`

**생성된 VIEW:**

1. **`v_daily_sales_official`**
   - daily_close 기준 공식 매출 뷰
   - 컬럼: store_id, date, total_sales, card_sales, cash_sales, visitors, memo, is_official(true), source('daily_close')
   - 공식 매출 SSOT 조회용

2. **`v_daily_sales_best_available`**
   - daily_close 있으면 daily_close
   - 없으면 sales + naver_visitors
   - 컬럼 통일
   - daily_close 있으면 is_official=true, source='daily_close'
   - sales만 있으면 is_official=false, source='sales'
   - 날짜별로 중복 없이 하나의 행만 반환

---

### ✅ STEP 2: daily_sales_items AUDIT 테이블 설계

**생성된 테이블:** `daily_sales_items_audit`

**필수 컬럼:**
- id (uuid, pk)
- store_id
- date
- menu_id
- action ('insert','update','soft_delete')
- old_qty
- new_qty
- source ('close','override','import')
- reason (text, nullable)
- changed_at (timestamptz default now())
- changed_by (uuid, nullable)

**인덱스:**
- idx_daily_sales_items_audit_store_date
- idx_daily_sales_items_audit_menu
- idx_daily_sales_items_audit_changed_at

**RLS 정책:**
- SELECT: 자신의 매장 데이터만 조회
- INSERT: SECURITY DEFINER 함수에서만 사용

---

### ✅ STEP 3: daily_sales_items 저장 정책 변경

**SQL 함수 수정:** `save_daily_close_transaction`

**변경사항:**
- ❌ DELETE 제거: `DELETE FROM daily_sales_items WHERE ...` 완전 제거
- ✅ UPSERT 구조: 메뉴 단위로 upsert하며 변경 이력 기록
- ✅ Audit 로깅: 모든 변경사항을 `daily_sales_items_audit`에 기록

**새 함수 추가:** `log_daily_sales_item_change`
- Audit 로깅 전용 헬퍼 함수
- SECURITY DEFINER로 실행

---

### ✅ STEP 4: 매출 저장 규칙 반영

**점장 마감 (`save_daily_close`):**
- ✅ daily_close upsert (공식 SSOT)
- ✅ sales upsert (파생 동기화)
- ✅ naver_visitors upsert (파생 동기화)
- ✅ daily_sales_items upsert + audit (source='close')

**매출 보정 (`save_sales`):**
- ✅ sales만 upsert
- ✅ daily_close는 절대 수정하지 않음
- (UI에 경고 추가 권장)

**판매량 보정 (`save_daily_sales_item`):**
- ✅ daily_sales_items upsert + audit (source='override')
- ✅ 절대 DELETE 금지

---

### ✅ STEP 5: 코드 수정

**파일:** `src/storage_supabase.py`

**수정된 함수:**
1. `save_daily_close()` - `p_changed_by` 파라미터 추가
2. `save_daily_sales_item()` - 완전 재작성 (overrides 제거, direct upsert + audit)

**추가된 함수:**
1. `load_official_daily_sales()` - 공식 매출 조회
2. `load_best_available_daily_sales()` - 최선의 매출 조회

---

## 🚀 실행 순서

### 1. SQL 실행 (Supabase SQL Editor)

1. Supabase 대시보드 접속
2. SQL Editor 열기
3. `sql/ssot_views_and_audit.sql` 파일 내용 복사
4. SQL Editor에 붙여넣기
5. 실행 (Run)

**확인사항:**
- ✅ VIEW 2개 생성 확인
- ✅ 테이블 1개 생성 확인 (daily_sales_items_audit)
- ✅ 함수 2개 생성/수정 확인 (log_daily_sales_item_change, save_daily_close_transaction)

---

### 2. 코드 배포

**변경된 파일:**
- `src/storage_supabase.py` (자동 적용)

**확인사항:**
- ✅ `save_daily_close()` 함수에 `p_changed_by` 전달 확인
- ✅ `save_daily_sales_item()` 함수가 `daily_sales_items`에 직접 저장하는지 확인
- ✅ Audit 로깅 함수 호출 확인

---

### 3. 테스트

#### 테스트 1: 점장 마감 저장
1. 점장 마감 페이지에서 데이터 입력
2. 저장 실행
3. `daily_sales_items` 테이블 확인 (upsert 확인)
4. `daily_sales_items_audit` 테이블 확인 (audit 기록 확인)

#### 테스트 2: 판매량 보정 저장
1. 판매량 보정 페이지에서 데이터 입력
2. 저장 실행
3. `daily_sales_items` 테이블 확인 (upsert 확인)
4. `daily_sales_items_audit` 테이블 확인 (source='override' 확인)

#### 테스트 3: VIEW 조회
1. `load_official_daily_sales()` 호출 테스트
2. `load_best_available_daily_sales()` 호출 테스트
3. `is_official`, `source` 컬럼 확인

---

## 📝 주의사항

### ⚠️ 중요

1. **daily_sales_items에서 DELETE 사용 금지**
   - 모든 코드에서 DELETE 제거 확인
   - qty=0으로 업데이트 + audit 기록

2. **공식 집계는 daily_close 기준**
   - `v_daily_sales_official` VIEW 사용
   - `is_official=true`인 데이터만 공식으로 간주

3. **sales만 있는 날짜는 is_official=false로 구분**
   - `v_daily_sales_best_available` VIEW에서 구분 가능

4. **모든 변경은 audit에 기록**
   - `daily_sales_items_audit` 테이블에 이력 저장
   - action: 'insert', 'update', 'soft_delete'
   - source: 'close', 'override', 'import'

---

## 🔍 문제 해결

### 문제 1: VIEW 조회 실패

**증상:** `v_daily_sales_official` 또는 `v_daily_sales_best_available` 조회 시 에러

**해결:**
1. SQL 실행 확인 (VIEW 생성 여부)
2. 권한 확인 (GRANT SELECT 확인)
3. 테이블 존재 확인 (daily_close, sales, naver_visitors)

---

### 문제 2: Audit 로깅 실패

**증상:** `log_daily_sales_item_change` RPC 호출 실패

**해결:**
1. 함수 생성 확인
2. 권한 확인 (GRANT EXECUTE 확인)
3. RLS 정책 확인 (INSERT 정책 확인)

**참고:** Audit 로깅 실패해도 저장은 계속 진행 (경고만 출력)

---

### 문제 3: daily_sales_items DELETE 에러

**증상:** 기존 코드에서 DELETE 사용 시 에러

**해결:**
1. 모든 DELETE 코드 제거 확인
2. UPSERT 구조로 변경 확인
3. qty=0으로 업데이트 + audit 기록

---

## 📊 데이터 확인 쿼리

### 공식 매출 조회
```sql
SELECT * FROM v_daily_sales_official 
WHERE store_id = 'your-store-id' 
ORDER BY date DESC 
LIMIT 10;
```

### 최선의 매출 조회
```sql
SELECT * FROM v_daily_sales_best_available 
WHERE store_id = 'your-store-id' 
ORDER BY date DESC 
LIMIT 10;
```

### Audit 이력 조회
```sql
SELECT * FROM daily_sales_items_audit 
WHERE store_id = 'your-store-id' 
ORDER BY changed_at DESC 
LIMIT 20;
```

---

## ✅ 체크리스트

### SQL 실행
- [ ] VIEW 2개 생성 확인
- [ ] 테이블 1개 생성 확인
- [ ] 함수 2개 생성/수정 확인
- [ ] 권한 설정 확인

### 코드 확인
- [ ] `save_daily_close()` 수정 확인
- [ ] `save_daily_sales_item()` 수정 확인
- [ ] `load_official_daily_sales()` 추가 확인
- [ ] `load_best_available_daily_sales()` 추가 확인

### 테스트
- [ ] 점장 마감 저장 테스트
- [ ] 판매량 보정 저장 테스트
- [ ] VIEW 조회 테스트
- [ ] Audit 기록 확인

---

## 📚 참고 문서

- `sql/ssot_views_and_audit.sql` - SQL 실행 파일
- `SSOT_구현_요약.md` - 구현 요약
- `storage_supabase_수정_요약.md` - 코드 수정 요약

---

**작성일:** 2026-01-23  
**버전:** v1.0
