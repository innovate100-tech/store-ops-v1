# 📊 DB 정리 요약 및 권장사항

## 🔍 발견된 문제점

### 1. 사용하지 않는 뷰 3개 (UNRESTRICTED 태그)
- `sales_from_daily_close` - 코드에서 사용 안 함
- `naver_visitors_from_daily_close` - 코드에서 사용 안 함  
- `daily_sales_items_from_daily_close` - 코드에서 사용 안 함

**문제:**
- 뷰가 만들어졌지만 실제 코드에서는 사용하지 않음
- UNRESTRICTED 태그로 보안 정책이 없음
- 불필요한 객체로 DB를 복잡하게 만듦

**해결:**
- `sql/cleanup_unused_views.sql` 실행하여 삭제

---

### 2. 중복 데이터 저장 (비효율적이지만 의도적)
- `daily_close` 테이블이 단일 소스
- 하지만 `sales`, `naver_visitors`, `daily_sales_items` 테이블에도 중복 저장
- 코드 주석: "호환성을 위해 기존 테이블에도 저장"

**현재 상태:**
- `save_daily_close()` 함수에서 4개 테이블에 동시 저장
- 데이터 일관성은 유지되지만 저장소 용량 낭비

**권장사항:**
- 현재는 유지 (기존 코드 호환성)
- 장기적으로는 뷰로 대체하거나 코드 마이그레이션 고려

---

### 3. 삭제된 테이블 매핑이 코드에 남아있음
- `src/storage_supabase.py`의 `table_mapping`에 다음이 포함됨:
  - `'suppliers.csv': 'suppliers'`
  - `'ingredient_suppliers.csv': 'ingredient_suppliers'`
  - `'orders.csv': 'orders'`

**문제:**
- 테이블은 삭제되었지만 코드 매핑은 남아있음
- 혼란을 야기할 수 있음

**해결:**
- 코드에서 해당 매핑 제거 (선택사항)

---

## ✅ 정리 작업

### 즉시 실행 가능 (권장)

1. **사용하지 않는 뷰 삭제**
   ```sql
   -- sql/cleanup_unused_views.sql 실행
   ```

### 선택적 정리

2. **코드 정리 (선택사항)**
   - `src/storage_supabase.py`에서 삭제된 테이블 매핑 제거

---

## 📋 현재 테이블 상태 (정상)

다음 테이블들은 모두 정상적으로 사용 중입니다:

✅ **핵심 테이블:**
- `stores` - 매장 정보
- `user_profiles` - 사용자 프로필
- `menu_master` - 메뉴 마스터
- `ingredients` - 재료 마스터
- `recipes` - 레시피
- `inventory` - 재고
- `daily_close` - 일일 마감 (단일 소스)
- `sales` - 매출 (daily_close에서 중복 저장)
- `naver_visitors` - 방문자수 (daily_close에서 중복 저장)
- `daily_sales_items` - 판매 내역 (daily_close에서 중복 저장)

✅ **분석/리포트 테이블:**
- `targets` - 목표 매출/비용
- `abc_history` - ABC 분석 히스토리
- `expense_structure` - 비용 구조
- `actual_settlement` - 실제 정산

---

## 🎯 권장 작업 순서

1. ✅ **사용하지 않는 뷰 삭제** (즉시 실행)
   - `sql/cleanup_unused_views.sql` 실행

2. ⚠️ **코드 정리** (선택사항)
   - `src/storage_supabase.py`에서 삭제된 테이블 매핑 제거

3. 📝 **장기 개선** (나중에 고려)
   - 중복 저장 로직 개선 (뷰 활용 또는 코드 마이그레이션)
