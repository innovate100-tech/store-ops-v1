# 매출/판매량 우선순위 정책 구현 완료

## 구현 완료 항목

### ✅ STEP 1: 매출 우선순위 고정
- **SQL 함수**: `sql/save_sales_with_daily_close_sync.sql`
  - `sales` 테이블을 SSOT로 저장
  - 동일 날짜에 `daily_close`가 존재하면 매출 필드도 동기화
  
- **Python 코드 수정**: `src/storage_supabase.py::save_sales()`
  - RPC 함수 `save_sales_with_daily_close_sync` 호출로 변경
  - `daily_close` 캐시도 무효화 추가

### ✅ STEP 2: 판매량 우선순위 레이어
- **SQL 테이블**: `sql/schema_daily_sales_items_overrides.sql`
  - `daily_sales_items_overrides` 테이블 생성
  - RLS 정책 적용
  
- **SQL 뷰**: `sql/view_daily_sales_items_effective.sql`
  - `v_daily_sales_items_effective` 뷰 생성
  - `daily_sales_items` (base) LEFT JOIN `overrides`
  - overrides가 있으면 overrides.qty 우선, 없으면 base.qty 사용

- **Python 코드 수정**:
  - `save_daily_sales_item()`: overrides 테이블에 upsert (누적 → 최종값 overwrite)
  - `load_csv()`: `daily_sales_items` → `v_daily_sales_items_effective` 뷰 사용
  - 컬럼명 매핑 로직 업데이트

### ✅ STEP 3: UI 경고 문구
- **점장 마감 화면**: 선택한 날짜에 overrides 존재 시 경고 표시
- **판매량 등록 화면**: "이 값은 마감 입력보다 우선(최종값)" 안내
- **매출 등록 화면**: "이 값은 마감 매출보다 우선(최종값)" 안내

## 실행 필요 작업

### 1. SQL 스크립트 실행 (Supabase SQL Editor)
```sql
-- STEP 1
\i sql/save_sales_with_daily_close_sync.sql

-- STEP 2
\i sql/schema_daily_sales_items_overrides.sql
\i sql/view_daily_sales_items_effective.sql
```

또는 Supabase Dashboard에서 각 SQL 파일 내용을 복사하여 실행

### 2. Python 코드 배포
- 변경된 파일들이 이미 반영됨
- 앱 재시작 필요

## 검증 체크리스트

### ✅ 매출 우선순위
- [ ] 매출등록 저장 시 `sales` 테이블에 저장됨
- [ ] 동일 날짜에 `daily_close`가 있으면 `daily_close.total_sales`도 동기화됨
- [ ] `sales`와 `daily_close` 매출 불일치가 사라짐

### ✅ 판매량 우선순위
- [ ] 판매량등록 저장 시 `daily_sales_items_overrides` 테이블에 저장됨
- [ ] 마감 입력 → 판매량등록 수정 → 분석/집계가 수정값 반영
- [ ] 판매량등록으로 수정된 메뉴 qty가 마감 재저장(DELETE+INSERT) 후에도 effective 기준으로 유지
- [ ] `v_daily_sales_items_effective` 뷰에서 overrides가 우선 적용됨

### ✅ 기존 기능 유지
- [ ] 기존 기능/화면 흐름은 그대로 유지
- [ ] 재료 사용량 집계가 정상 동작
- [ ] 판매 분석이 정상 동작
- [ ] 대시보드가 정상 동작

## 주의사항

1. **기존 데이터 영향 없음**: 
   - overrides 테이블은 새로 생성되므로 기존 데이터에 영향 없음
   - 뷰는 기존 daily_sales_items를 그대로 사용

2. **마감 재저장 시**:
   - 마감이 daily_sales_items를 DELETE+INSERT 해도
   - overrides가 있으면 effective 뷰에서 자동으로 overrides 값이 우선 적용됨
   - **데이터 유실 없음**

3. **성능**:
   - 뷰는 FULL OUTER JOIN을 사용하므로 대량 데이터 시 성능 모니터링 필요
   - 필요시 인덱스 추가 고려

## 롤백 방법

문제 발생 시:

```sql
-- 뷰 삭제
DROP VIEW IF EXISTS v_daily_sales_items_effective;

-- 테이블 삭제 (주의: 데이터 삭제됨)
DROP TABLE IF EXISTS daily_sales_items_overrides CASCADE;

-- 함수 삭제
DROP FUNCTION IF EXISTS save_sales_with_daily_close_sync;
```

그 후 Python 코드의 변경사항도 되돌려야 합니다.
