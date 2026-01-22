# 빠른 수정: 뷰가 생성되지 않아 데이터가 안 보이는 경우

## 문제
판매관리, 재료사용량 집계 페이지에서 "데이터가 없다"고 표시되는 경우

## 원인
`v_daily_sales_items_effective` 뷰가 아직 생성되지 않았을 가능성이 높습니다.

## 해결 방법

### 방법 1: SQL 스크립트 실행 (권장)

Supabase SQL Editor에서 다음을 실행:

```sql
-- 1. overrides 테이블 생성
\i sql/schema_daily_sales_items_overrides.sql

-- 2. 우선순위 뷰 생성
\i sql/view_daily_sales_items_effective.sql
```

또는 Supabase Dashboard → SQL Editor에서 각 파일 내용을 복사하여 실행

### 방법 2: 임시 해결 (뷰 없이 사용)

뷰가 없어도 기존 `daily_sales_items` 테이블로 자동 fallback되도록 코드가 수정되었습니다.

하지만 **우선순위 정책이 작동하지 않습니다** (판매량등록이 마감보다 우선 적용되지 않음).

## 확인 방법

뷰가 생성되었는지 확인:

```sql
-- 뷰 존재 확인
SELECT * FROM information_schema.views 
WHERE table_name = 'v_daily_sales_items_effective';

-- 뷰 조회 테스트
SELECT * FROM v_daily_sales_items_effective LIMIT 5;
```

## 주의사항

- 뷰가 없으면 기존 `daily_sales_items` 테이블을 사용하므로 데이터는 보입니다
- 하지만 **우선순위 정책(매출등록/판매량등록 우선)**이 작동하지 않습니다
- 정상 작동을 위해서는 반드시 뷰를 생성해야 합니다
