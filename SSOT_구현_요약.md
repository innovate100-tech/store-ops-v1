# SSOT 구현 요약

## 실행 순서

### 1. SQL 실행 (Supabase SQL Editor)

`sql/ssot_views_and_audit.sql` 파일의 내용을 Supabase SQL Editor에서 실행하세요.

**포함 내용:**
- `v_daily_sales_official` VIEW 생성
- `v_daily_sales_best_available` VIEW 생성
- `daily_sales_items_audit` 테이블 생성
- `log_daily_sales_item_change` 함수 생성
- `save_daily_close_transaction` 함수 수정 (DELETE 제거, UPSERT + audit)

---

## 주요 변경사항

### 1. SSOT 정책 확립

- **공식 매출 SSOT**: `daily_close` 테이블
- **보조 입력 채널**: `sales` 테이블 (마감 못한 날/과거 입력용)
- **VIEW로 구분**: `is_official`, `source` 컬럼으로 공식/보조 구분

### 2. daily_sales_items 저장 정책 변경

**이전 (❌):**
```sql
DELETE FROM daily_sales_items WHERE store_id=? AND date=?;
INSERT INTO daily_sales_items ...;
```

**변경 후 (✅):**
```sql
-- 메뉴 단위 UPSERT
INSERT INTO daily_sales_items (...) 
ON CONFLICT (store_id, date, menu_id) DO UPDATE SET qty = EXCLUDED.qty;

-- Audit 로깅
INSERT INTO daily_sales_items_audit (...);
```

### 3. 저장 규칙

#### 점장 마감 (`save_daily_close`)
- `daily_close` upsert (공식 SSOT)
- `sales` upsert (파생 동기화)
- `naver_visitors` upsert (파생 동기화)
- `daily_sales_items` upsert + audit (source='close')

#### 매출 보정 (`save_sales`)
- `sales`만 upsert
- `daily_close`는 절대 수정하지 않음
- (UI에 경고 추가 권장)

#### 판매량 보정 (`save_daily_sales_item`)
- `daily_sales_items` upsert + audit (source='override')
- 절대 DELETE 금지

---

## 코드 수정 사항

### `src/storage_supabase.py`

1. **`save_daily_close()` 수정**
   - `p_changed_by` 파라미터 추가 (audit용)
   - RPC 호출 시 `p_changed_by` 전달

2. **`save_daily_sales_item()` 수정**
   - `daily_sales_items_overrides` 대신 `daily_sales_items`에 직접 upsert
   - Audit 로깅 추가
   - DELETE 금지, UPSERT 구조로 변경

3. **새 함수 추가**
   - `load_official_daily_sales()`: 공식 매출 조회 (daily_close 기준)
   - `load_best_available_daily_sales()`: 최선의 매출 조회 (daily_close 우선)

---

## 주의사항

### ⚠️ 중요

1. **daily_sales_items에서 DELETE 사용 금지**
   - 모든 코드에서 DELETE 제거
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

## 테스트 체크리스트

- [ ] SQL 실행 완료 (VIEW, 테이블, 함수 생성)
- [ ] 점장 마감 저장 테스트 (daily_sales_items upsert 확인)
- [ ] 판매량 보정 저장 테스트 (audit 기록 확인)
- [ ] VIEW 조회 테스트 (공식/보조 구분 확인)
- [ ] DELETE 금지 확인 (기존 DELETE 코드 제거 확인)

---

## 마이그레이션 가이드

기존 데이터는 그대로 유지되며, 새로운 정책이 적용됩니다.

1. SQL 실행 후 기존 데이터 확인
2. 점장 마감 저장 테스트
3. 판매량 보정 저장 테스트
4. VIEW 조회 테스트

문제 발생 시 `daily_sales_items_audit` 테이블에서 변경 이력을 확인할 수 있습니다.
