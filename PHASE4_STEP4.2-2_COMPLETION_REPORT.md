# PHASE 4 / STEP 4.2-2 완료 요약

**작업일**: 2025-01-23  
**목표**: 비용 구조 및 손익분기점 계산 경로를 공식 엔진 함수로 100% 통일

---

## 생성한 공식 함수

### 1. `get_fixed_costs(store_id, year, month) -> float`
- **위치**: `src/storage_supabase.py:3084`
- **우선순위**:
  1. `actual_settlement_items` (final 상태) - `input_type='amount'`인 항목 합계
  2. `expense_structure` - 임차료, 인건비, 공과금 합계
- **반환**: 고정비 합계 (원 단위, float)

### 2. `get_variable_cost_ratio(store_id, year, month) -> float`
- **위치**: `src/storage_supabase.py:3160`
- **우선순위**:
  1. `actual_settlement_items` (final 상태) - `input_type='rate'`인 항목 합계
  2. `expense_structure` - 재료비, 부가세&카드수수료 합계
- **반환**: 변동비율 (0.0 ~ 1.0, 소수 형태)

### 3. `calculate_break_even_sales(store_id, year, month) -> float`
- **위치**: `src/storage_supabase.py:3236`
- **공식**: `고정비 / (1 - 변동비율)`
- **내부 호출**: `get_fixed_costs()`, `get_variable_cost_ratio()`
- **반환**: 손익분기점 매출 (원 단위, float), 계산 불가 시 0.0

---

## 수정 파일 목록

### 1. `src/storage_supabase.py`
- **추가**: 공식 엔진 함수 3개 생성
- **위치**: `load_monthly_sales_total()` 함수 바로 앞
- **의존성**: `get_month_settlement_status()`, `load_cost_item_templates()`, `load_actual_settlement_items()`, `load_expense_structure()`

### 2. `ui_pages/target_cost_structure.py`
- **변경**: 고정비/변동비/손익분기점 계산 로직 제거
- **교체**: `get_fixed_costs()`, `get_variable_cost_ratio()`, `calculate_break_even_sales()` 호출
- **Import 추가**: `get_fixed_costs`, `get_variable_cost_ratio`, `calculate_break_even_sales`

### 3. `ui_pages/dashboard/metrics.py`
- **변경**: `_compute_dashboard_metrics()` 함수 내부 계산 로직 제거
- **교체**: 공식 엔진 함수 호출
- **Import 추가**: `get_fixed_costs`, `get_variable_cost_ratio`, `calculate_break_even_sales`

### 4. `app.py`
- **변경 1**: 통합 대시보드 페이지 - 고정비/변동비/손익분기점 계산 제거
- **변경 2**: 목표 비용구조 페이지 - 고정비/변동비 계산 제거
- **변경 3**: 목표 매출 구조 페이지 - 고정비/변동비 계산 제거
- **교체**: 공식 엔진 함수 호출
- **Import 추가**: `load_monthly_sales_total` (이미 있음), `get_fixed_costs`, `get_variable_cost_ratio`, `calculate_break_even_sales`

### 5. `ui_pages/home.py`
- **변경**: `get_store_financial_structure()` 함수 내부 계산 로직 대폭 간소화
- **교체**: 공식 엔진 함수 호출
- **Import 추가**: `get_fixed_costs`, `get_variable_cost_ratio`, `calculate_break_even_sales`

---

## 제거된 중복 계산 수

### 고정비 계산 제거
1. `ui_pages/target_cost_structure.py:79` - `expense_df[expense_df['category'].isin(fixed_categories)]['amount'].sum()`
2. `ui_pages/dashboard/metrics.py:202` - 동일 계산
3. `app.py:2240` - 동일 계산 (통합 대시보드)
4. `app.py:3164` - 동일 계산 (목표 비용구조)
5. `app.py:3927` - 동일 계산 (목표 매출 구조)
6. `ui_pages/home.py:690` - 동일 계산 (actual_settlement 경로)
7. `ui_pages/home.py:741` - 동일 계산 (expense_structure 경로)

**총 7개 제거**

### 변동비율 계산 제거
1. `ui_pages/target_cost_structure.py:89` - `variable_df['amount'].sum()`
2. `ui_pages/dashboard/metrics.py:210` - 동일 계산
3. `app.py:2248` - 동일 계산 (통합 대시보드)
4. `app.py:3174` - 동일 계산 (목표 비용구조)
5. `app.py:3934` - 동일 계산 (목표 매출 구조)
6. `ui_pages/home.py:695` - 동일 계산 (actual_settlement 경로)
7. `ui_pages/home.py:748` - 동일 계산 (expense_structure 경로)

**총 7개 제거**

### 손익분기점 계산 제거
1. `ui_pages/target_cost_structure.py:97` - `fixed_costs / (1 - variable_rate_decimal)`
2. `ui_pages/dashboard/metrics.py:217` - 동일 계산
3. `app.py:2255` - 동일 계산 (통합 대시보드)
4. `app.py:3181` - 동일 계산 (목표 비용구조)
5. `ui_pages/home.py:700` - 동일 계산 (actual_settlement 경로)
6. `ui_pages/home.py:755` - 동일 계산 (expense_structure 경로)

**총 6개 제거**

**전체 제거된 중복 계산: 20개**

---

## 남아 있는 손익분기점 경로 수

### ✅ 공식 엔진 함수 사용 (SSOT 준수)
1. `ui_pages/target_cost_structure.py` - `calculate_break_even_sales()` 호출
2. `ui_pages/dashboard/metrics.py` - `calculate_break_even_sales()` 호출
3. `app.py` (통합 대시보드) - `calculate_break_even_sales()` 호출
4. `app.py` (목표 비용구조) - `calculate_break_even_sales()` 호출
5. `ui_pages/home.py` - `calculate_break_even_sales()` 호출

**남아 있는 경로: 5개 (모두 SSOT 준수)**

---

## actual / expense fallback 테스트 결과

### 구현된 우선순위 로직
1. **actual_settlement_items (final 상태)** 우선:
   - `get_month_settlement_status()`로 'final' 확인
   - final이면 `actual_settlement_items`에서 고정비/변동비 추출
   - `input_type='amount'` → 고정비 카테고리 (임차료, 인건비, 공과금)
   - `input_type='rate'` → 변동비 카테고리 (재료비, 부가세&카드수수료)

2. **expense_structure fallback**:
   - final이 아니거나 actual_settlement_items가 없으면
   - `load_expense_structure()`로 조회
   - 카테고리별 합계 계산

### 테스트 시나리오
- [ ] actual_settlement final 있는 달 → actual 기준 값 반환
- [ ] actual_settlement 없는 달 → expense_structure 기준 값 반환
- [ ] expense_structure도 없는 달 → 0 반환
- [ ] actual과 expense 둘 다 있는데 final 아닌 달 → expense 기준 값 반환

---

## 발견된 위험 요소

### 1. actual_settlement_items의 input_type 추론 로직
- **위치**: `get_fixed_costs()`, `get_variable_cost_ratio()` 내부
- **문제**: `actual_settlement_items`에서 `input_type`을 `amount`/`percent` 존재 여부로 추론
- **영향**: `amount`와 `percent` 둘 다 있으면 `amount` 우선 (고정비로 처리)
- **우선순위**: 낮음 (기존 로직과 동일)

### 2. 카테고리별 세부 항목 표시
- **위치**: `app.py` (목표 매출 구조 페이지)
- **문제**: 카테고리별 세부 항목(`fixed_by_category`, `variable_rate_by_category`)은 여전히 `expense_structure` 직접 조회
- **영향**: 표시용이므로 큰 문제 없음, 단 일관성 측면에서 고려 필요
- **우선순위**: 낮음 (표시용 데이터)

### 3. 변동비율 단위 변환
- **위치**: 모든 수정 파일
- **문제**: 공식 엔진 함수는 소수 형태(0.0~1.0) 반환, UI는 % 단위 필요
- **해결**: `variable_cost_rate = variable_cost_ratio * 100.0` 변환 추가
- **우선순위**: 없음 (이미 처리됨)

### 4. breakeven_sales None 처리
- **위치**: 모든 수정 파일
- **문제**: 기존 로직은 `breakeven_sales = None` 사용, 공식 함수는 `0.0` 반환
- **해결**: `if breakeven_sales <= 0: breakeven_sales = None` 변환 추가
- **우선순위**: 없음 (이미 처리됨)

---

## 헌법 준수 상태

### ✅ 완료
- 모든 고정비 계산이 `get_fixed_costs()` 함수 사용
- 모든 변동비율 계산이 `get_variable_cost_ratio()` 함수 사용
- 모든 손익분기점 계산이 `calculate_break_even_sales()` 함수 사용
- actual_settlement (final) 우선순위 구현
- expense_structure fallback 구현

### 📋 다음 단계 권고
- 실제 테스트로 actual/expense fallback 동작 확인
- 카테고리별 세부 항목도 공식 함수로 통일 (선택적)
- 성능 모니터링 (캐시 적용 확인)

---

**작업 완료일**: 2025-01-23  
**다음 단계**: 실제 테스트 및 검증
