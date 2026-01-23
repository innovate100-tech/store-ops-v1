# Phase 8-A Step 7: store_id 필터 강제 적용 검증

## 목표
모든 데이터 로더/저장 함수에서 `store_id` 필터가 강제 적용되는지 확인 및 누락된 필터 추가

## 검증 방법

### 1. 주요 함수 검증 체크리스트

#### ✅ 이미 store_id 필터 적용된 함수:
- `load_csv()` - `.eq("store_id", store_id)` 적용
- `load_key_menus()` - `.eq("store_id", store_id)` 적용
- `save_sales()` - RPC 함수에 `p_store_id` 전달
- `save_daily_close()` - RPC 함수에 `p_store_id` 전달
- `save_menu()` - `.eq("store_id", store_id)` 적용
- `save_ingredient()` - `.eq("store_id", store_id)` 적용
- `save_recipe()` - store_id 필터 확인 필요
- `load_expense_structure()` - `.eq("store_id", store_id)` 적용
- `load_cost_item_templates()` - `.eq("store_id", store_id)` 적용
- `load_actual_settlement_items()` - `.eq("store_id", store_id)` 적용
- `load_monthly_sales_total()` - `.eq("store_id", store_id)` 적용

#### ⚠️ 확인 필요:
- `.in_("id", ids)` 사용 시 store_id 필터 추가 필요 여부 확인
- `load_expense_structure_range()` - store_id 필터 확인
- 외래키 조회 시 store_id 필터 확인

### 2. 검증 쿼리

다음 SQL로 각 테이블의 store_id 필터가 제대로 적용되는지 확인:

```sql
-- 예시: menu_master 테이블에서 store_id 필터 확인
SELECT COUNT(*) as total_count
FROM menu_master
WHERE store_id = '현재_store_id';

-- RLS 정책 확인
SELECT * FROM pg_policies 
WHERE tablename = 'menu_master';
```

### 3. 수정 사항

#### 수정 1: `.in_()` 사용 시 store_id 필터 추가
- `_load_csv_impl()` 내부의 `.in_("id", ids)` 쿼리에 `.eq("store_id", store_id)` 추가

#### 수정 2: `load_expense_structure_range()` store_id 필터 확인
- 함수 내부에서 `get_current_store_id()` 호출 및 필터 적용 확인

### 4. 테스트 시나리오

1. **다중 매장 사용자로 로그인**
   - 매장 A 선택
   - 데이터 조회/저장 시 매장 A 데이터만 접근 가능한지 확인

2. **매장 전환 테스트**
   - 매장 A → 매장 B 전환
   - 데이터가 매장 B 데이터로 변경되는지 확인

3. **RLS 정책 테스트**
   - 다른 매장의 데이터에 접근 시도 시 차단되는지 확인

## 완료 기준

- [ ] 모든 데이터 로더 함수에서 store_id 필터 적용 확인
- [ ] 모든 저장 함수에서 store_id 필터 적용 확인
- [ ] `.in_()` 사용 시 store_id 필터 추가
- [ ] 다중 매장 환경에서 테스트 완료
- [ ] RLS 정책과 함께 동작 확인
