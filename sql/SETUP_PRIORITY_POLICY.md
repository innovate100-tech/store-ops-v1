# 매출/판매량 우선순위 정책 설정 가이드

## 개요
"마감이 있어도 매출등록/판매량등록이 우선" 정책을 시스템적으로 보장하기 위한 SQL 스크립트 실행 가이드입니다.

## 실행 순서

### 1. STEP 1: 매출 우선순위 고정
```sql
-- 매출 저장 + daily_close 동기화 함수
\i sql/save_sales_with_daily_close_sync.sql
```

### 2. STEP 2: 판매량 우선순위 레이어
```sql
-- 2-1. overrides 테이블 생성
\i sql/schema_daily_sales_items_overrides.sql

-- 2-2. 우선순위 뷰 생성
\i sql/view_daily_sales_items_effective.sql
```

## 검증 쿼리

### 매출 동기화 확인
```sql
-- 같은 날짜의 sales와 daily_close 매출이 일치하는지 확인
SELECT 
    s.date,
    s.total_sales AS sales_total,
    dc.total_sales AS daily_close_total,
    CASE WHEN s.total_sales = dc.total_sales THEN '일치' ELSE '불일치' END AS status
FROM sales s
LEFT JOIN daily_close dc ON s.store_id = dc.store_id AND s.date = dc.date
WHERE s.store_id = 'your-store-id'
ORDER BY s.date DESC
LIMIT 10;
```

### 판매량 우선순위 확인
```sql
-- overrides가 있는 날짜 확인
SELECT 
    sale_date,
    COUNT(*) AS override_count
FROM daily_sales_items_overrides
WHERE store_id = 'your-store-id'
GROUP BY sale_date
ORDER BY sale_date DESC
LIMIT 10;

-- effective 뷰에서 우선순위 적용 확인
SELECT 
    date,
    menu_id,
    qty,
    source_type  -- 'override' 또는 'base'
FROM v_daily_sales_items_effective
WHERE store_id = 'your-store-id'
    AND date = '2024-01-20'
ORDER BY menu_id;
```

## 주의사항

1. **기존 데이터 영향 없음**: 
   - overrides 테이블은 새로 생성되므로 기존 데이터에 영향 없음
   - 뷰는 기존 daily_sales_items를 그대로 사용하되, overrides가 있으면 우선 적용

2. **마감 재저장 시**:
   - 마감이 daily_sales_items를 DELETE+INSERT 해도
   - overrides가 있으면 effective 뷰에서 자동으로 overrides 값이 우선 적용됨
   - **데이터 유실 없음**

3. **성능**:
   - 뷰는 FULL OUTER JOIN을 사용하므로 대량 데이터 시 성능 모니터링 필요
   - 필요시 인덱스 추가 고려

## 롤백 방법

만약 문제가 발생하면:

```sql
-- 뷰 삭제
DROP VIEW IF EXISTS v_daily_sales_items_effective;

-- 테이블 삭제 (주의: 데이터 삭제됨)
DROP TABLE IF EXISTS daily_sales_items_overrides CASCADE;

-- 함수 삭제
DROP FUNCTION IF EXISTS save_sales_with_daily_close_sync;
```

그 후 Python 코드의 변경사항도 되돌려야 합니다.
