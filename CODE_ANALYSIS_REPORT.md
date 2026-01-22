# 코드 크기 분석 리포트

## 1. 파일별 LOC TOP 10

| 순위 | 파일명 | 라인 수 |
|------|--------|---------|
| 1 | app.py | 4,035 lines |
| 2 | ui_pages/settlement_actual.py | 1,731 lines |
| 3 | ui_pages/dashboard.py | 1,184 lines |
| 4 | ui_pages/target_cost_structure.py | 945 lines |
| 5 | ui_pages/sales_management.py | 597 lines |
| 6 | ui_pages/recipe_management.py | 593 lines |
| 7 | ui_pages/ingredient_management.py | 584 lines |
| 8 | ui_pages/menu_management.py | 451 lines |
| 9 | ui_pages/sales_analysis.py | 389 lines |
| 10 | ui_pages/target_sales_structure.py | 246 lines |

## 2. 함수별 LOC TOP 20 (render_* 우선)

| 순위 | 파일명 | 함수명 | 라인 수 |
|------|--------|--------|---------|
| 1 | ui_pages/recipe_management.py | render_recipe_management | 579 lines |
| 2 | ui_pages/sales_management.py | render_sales_management | 574 lines |
| 3 | ui_pages/dashboard.py | render_dashboard | 548 lines |
| 4 | ui_pages/menu_management.py | render_menu_management | 436 lines |
| 5 | ui_pages/target_cost_structure.py | render_target_cost_structure | 424 lines |
| 6 | ui_pages/target_sales_structure.py | render_target_sales_structure | 231 lines |
| 7 | ui_pages/sales_entry.py | render_sales_entry | 180 lines |
| 8 | ui_pages/sales_analysis.py | render_sales_analysis | 149 lines |
| 9 | ui_pages/manager_close.py | render_manager_close | 121 lines |
| 10 | ui_pages/ingredient_management.py | render_ingredient_management | 111 lines |

---

## 3. TOP 5 긴 페이지 상세 분석

### 3.1 app.py (4,035 lines)

**현재 상태:**
- 메인 앱 파일로 라우팅과 진단 기능 포함
- `_diagnose_supabase_connection()` 함수가 매우 길 것으로 추정

**UI 렌더 코드 비율:** 약 20-30%
- `st.write`, `st.error`, `st.json` 등 진단 출력 반복

**데이터 조회 코드:** 약 10-15%
- Supabase 연결 테스트 쿼리들

**데이터 가공 코드:** 거의 없음

**상태/필터:** 없음

**중복 패턴 후보:**
1. 진단 섹션의 반복적인 `st.write` + `st.json` 패턴
2. 에러 처리 블록의 반복

**분리 권장 구조:**
```
app.py (라우팅만, ~200 lines)
  └─ src/diagnostics/supabase_diagnosis.py (~300 lines)
```

**결론:** ✅ **쪼개야 하는 페이지**
- 진단 기능을 별도 모듈로 분리
- 라우팅 로직만 남기기

---

### 3.2 ui_pages/settlement_actual.py (1,731 lines)

**현재 상태:**
- `render_settlement_actual()`: 46 lines (매우 짧음!)
- 하지만 파일 전체는 1,731 lines
- 헬퍼 함수들이 매우 많음:
  - `set_state()`: 상태 추적 래퍼
  - `_load_sales_with_filter()`: 60 lines
  - `_load_actual_settlement_with_filter()`: 49 lines
  - `_show_settlement_query_diagnostics()`: 185 lines
  - `load_actual_settlement_data()`: 219 lines
  - `_timed_db_query()`: 30 lines

**UI 렌더 코드 비율:** 약 40-50%
- `render_settlement_actual()` 내부에 많은 `st.*` 호출
- 진단 섹션의 반복적인 출력

**데이터 조회 코드:** 약 30-40%
- `_load_sales_with_filter()`, `_load_actual_settlement_with_filter()`
- `load_actual_settlement_data()` 내부의 복잡한 쿼리 로직

**데이터 가공 코드:** 약 10-20%
- pandas 필터링 및 집계

**상태/필터:**
- `year`, `month`, `store_id` 필터링
- 복잡한 상태 관리 (`set_state` 래퍼 사용)

**중복 패턴 후보:**
1. 데이터 로드 함수들의 유사한 구조 (필터 적용 → 쿼리 실행 → 에러 처리)
2. 진단 출력의 반복 패턴
3. 상태 추적 코드의 반복

**분리 권장 구조:**
```
settlement_actual.py (render 함수만, ~200 lines)
  ├─ ui_pages/settlement_actual/
  │   ├─ data_loaders.py (~300 lines)
  │   │   ├─ _load_sales_with_filter()
  │   │   ├─ _load_actual_settlement_with_filter()
  │   │   └─ load_actual_settlement_data()
  │   ├─ diagnostics.py (~200 lines)
  │   │   └─ _show_settlement_query_diagnostics()
  │   └─ state_manager.py (~100 lines)
  │       └─ set_state() 및 상태 추적 로직
```

**결론:** ✅ **쪼개야 하는 페이지**
- 헬퍼 함수들이 너무 많음
- 데이터 로더와 진단 기능 분리 필요

---

### 3.3 ui_pages/dashboard.py (1,184 lines, render_dashboard: 548 lines)

**현재 상태:**
- `render_dashboard()`: 548 lines
- `_show_query_diagnostics()`: 292 lines
- `compute_merged_sales_visitors()`: 100+ lines
- `compute_monthly_summary()`: 60+ lines
- `compute_menu_sales_summary()`: 180+ lines

**UI 렌더 코드 비율:** 약 50-60%
- 많은 `st.markdown`, `st.metric`, `st.columns` 호출
- 반복적인 섹션 헤더 렌더링

**데이터 조회 코드:** 약 20-30%
- `load_csv()` 호출이 많음 (sales, visitors, targets, menu, recipes, ingredients 등)
- `load_expense_structure()` 호출
- 직접 Supabase 쿼리 (진단용)

**데이터 가공 코드:** 약 20-30%
- `merge_sales_visitors()`: pandas merge
- `groupby()` 집계 (월별, 메뉴별)
- `apply()` 함수로 포맷팅 (금액, 비율 등)

**상태/필터:**
- `current_year`, `current_month` (KST 기준)
- `store_id` 필터링

**중복 패턴 후보:**
1. 섹션 헤더 렌더링 패턴 반복 (`st.markdown` + HTML)
2. 데이터 로드 → 필터링 → 집계 패턴 반복
3. `st.metric` 카드 렌더링 반복
4. `apply()` 함수로 포맷팅하는 패턴 반복

**분리 권장 구조:**
```
dashboard.py (render 함수만, ~300 lines)
  ├─ ui_pages/dashboard/
  │   ├─ data_loaders.py (~150 lines)
  │   │   └─ 모든 load_csv() 호출을 함수로 그룹화
  │   ├─ data_transformers.py (~200 lines)
  │   │   ├─ compute_merged_sales_visitors()
  │   │   ├─ compute_monthly_summary()
  │   │   └─ compute_menu_sales_summary()
  │   ├─ ui_sections.py (~200 lines)
  │   │   ├─ render_kpi_cards()
  │   │   ├─ render_breakeven_section()
  │   │   ├─ render_sales_charts()
  │   │   └─ render_menu_analysis()
  │   └─ diagnostics.py (~300 lines)
  │       └─ _show_query_diagnostics()
```

**결론:** ✅ **쪼개야 하는 페이지**
- UI 섹션별로 분리 가능
- 데이터 변환 로직 분리 필요

---

### 3.4 ui_pages/target_cost_structure.py (945 lines, render_target_cost_structure: 424 lines)

**현재 상태:**
- `render_target_cost_structure()`: 424 lines
- 파일 전체: 945 lines (다른 헬퍼 함수들 포함)

**UI 렌더 코드 비율:** 약 60-70%
- 매우 많은 `st.number_input`, `st.button`, `st.dataframe` 호출
- 반복적인 입력 폼 렌더링
- 테이블 편집 UI

**데이터 조회 코드:** 약 15-20%
- `load_expense_structure()` 호출
- `load_csv('targets.csv')` 호출
- `save_expense_item()`, `update_expense_item()`, `delete_expense_item()` 호출

**데이터 가공 코드:** 약 10-15%
- 손익분기점 계산 로직
- 고정비/변동비 계산
- pandas 필터링

**상태/필터:**
- `selected_year`, `selected_month` (number_input으로 선택)
- `store_id` (자동)

**중복 패턴 후보:**
1. 비용 항목 입력 폼의 반복 패턴
2. 테이블 편집 UI의 반복 (저장/수정/삭제 버튼)
3. 계산 로직의 반복 (고정비, 변동비, 손익분기점)

**분리 권장 구조:**
```
target_cost_structure.py (render 함수만, ~200 lines)
  ├─ ui_pages/target_cost_structure/
  │   ├─ calculations.py (~100 lines)
  │   │   ├─ calculate_fixed_costs()
  │   │   ├─ calculate_variable_cost_rate()
  │   │   └─ calculate_breakeven_sales()
  │   ├─ ui_forms.py (~200 lines)
  │   │   ├─ render_expense_input_form()
  │   │   └─ render_expense_table()
  │   └─ data_handlers.py (~150 lines)
  │       └─ CRUD 작업 래퍼 함수들
```

**결론:** ✅ **쪼개야 하는 페이지**
- 계산 로직과 UI 폼 분리 필요
- CRUD 작업 그룹화

---

### 3.5 ui_pages/sales_management.py (597 lines, render_sales_management: 574 lines)

**현재 상태:**
- `render_sales_management()`: 574 lines (거의 파일 전체)
- 단일 큰 함수

**UI 렌더 코드 비율:** 약 55-65%
- 많은 `st.markdown`, `st.metric`, `st.columns` 호출
- 차트 렌더링 (plotly)
- 반복적인 섹션 구조

**데이터 조회 코드:** 약 20-25%
- `load_csv('sales.csv')`
- `load_csv('naver_visitors.csv')`
- `load_csv('targets.csv')`

**데이터 가공 코드:** 약 15-20%
- `merge_sales_visitors()` 호출
- pandas `groupby()` 집계 (월별, 주별)
- 전월/전년 대비 계산

**상태/필터:**
- `current_year`, `current_month` (KST 기준)
- `store_id` (자동)

**중복 패턴 후보:**
1. 섹션 헤더 + 메트릭 카드 패턴 반복
2. 기간별 비교 로직 반복 (전월, 전년)
3. 차트 렌더링 패턴 반복

**분리 권장 구조:**
```
sales_management.py (render 함수만, ~200 lines)
  ├─ ui_pages/sales_management/
  │   ├─ data_loaders.py (~100 lines)
  │   │   └─ load_sales_data() (통합 로더)
  │   ├─ analytics.py (~150 lines)
  │   │   ├─ calculate_period_comparison()
  │   │   └─ calculate_trends()
  │   └─ ui_sections.py (~200 lines)
  │       ├─ render_kpi_section()
  │       ├─ render_period_comparison()
  │       └─ render_charts()
```

**결론:** ✅ **쪼개야 하는 페이지**
- 섹션별 UI 분리 가능
- 분석 로직 분리 필요

---

## 4. 결론 및 리팩토링 계획

### 4.1 "길어도 되는 페이지" vs "쪼개야 하는 페이지"

#### ✅ **쪼개야 하는 페이지 (5개)**
1. **app.py** - 진단 기능 분리 필요
2. **settlement_actual.py** - 헬퍼 함수들이 너무 많음
3. **dashboard.py** - 섹션별 분리 가능
4. **target_cost_structure.py** - 계산/UI/CRUD 분리 필요
5. **sales_management.py** - 섹션별 분리 가능

#### ⚠️ **길어도 되는 페이지 (검토 필요)**
- **recipe_management.py** (593 lines) - 복잡한 레시피 편집 UI이므로 일단 유지
- **menu_management.py** (451 lines) - 메뉴 관리의 복잡성 고려 시 적절할 수 있음

### 4.2 1단계 리팩토링 계획 (안전하게, 페이지 1개씩)

#### Phase 1-1: settlement_actual.py 분리 (우선순위: 높음)

**목표:** 헬퍼 함수들을 별도 모듈로 분리

**단계:**
1. `ui_pages/settlement_actual/` 폴더 생성
2. `data_loaders.py` 생성 → 데이터 로드 함수들 이동
3. `diagnostics.py` 생성 → 진단 함수 이동
4. `state_manager.py` 생성 → 상태 관리 함수 이동
5. `settlement_actual.py`는 render 함수만 남기기

**예상 결과:**
- `settlement_actual.py`: ~200 lines
- `data_loaders.py`: ~300 lines
- `diagnostics.py`: ~200 lines
- `state_manager.py`: ~100 lines

**테스트:** 기존 동작 100% 유지 확인

---

#### Phase 1-2: dashboard.py 분리 (우선순위: 중간)

**목표:** UI 섹션과 데이터 변환 로직 분리

**단계:**
1. `ui_pages/dashboard/` 폴더 생성
2. `data_transformers.py` 생성 → compute 함수들 이동
3. `ui_sections.py` 생성 → 섹션별 렌더 함수 추출
4. `diagnostics.py` 생성 → 진단 함수 이동
5. `dashboard.py`는 render 함수와 섹션 호출만 남기기

**예상 결과:**
- `dashboard.py`: ~300 lines
- `data_transformers.py`: ~200 lines
- `ui_sections.py`: ~200 lines
- `diagnostics.py`: ~300 lines

**테스트:** 모든 차트와 메트릭이 정상 표시되는지 확인

---

#### Phase 1-3: target_cost_structure.py 분리 (우선순위: 중간)

**목표:** 계산 로직과 UI 폼 분리

**단계:**
1. `ui_pages/target_cost_structure/` 폴더 생성
2. `calculations.py` 생성 → 계산 함수들 이동
3. `ui_forms.py` 생성 → 폼 렌더 함수 추출
4. `target_cost_structure.py`는 render 함수만 남기기

**예상 결과:**
- `target_cost_structure.py`: ~200 lines
- `calculations.py`: ~100 lines
- `ui_forms.py`: ~200 lines

**테스트:** 모든 CRUD 작업이 정상 동작하는지 확인

---

#### Phase 1-4: sales_management.py 분리 (우선순위: 낮음)

**목표:** 섹션별 UI 분리

**단계:**
1. `ui_pages/sales_management/` 폴더 생성
2. `analytics.py` 생성 → 분석 함수들 이동
3. `ui_sections.py` 생성 → 섹션별 렌더 함수 추출
4. `sales_management.py`는 render 함수만 남기기

**예상 결과:**
- `sales_management.py`: ~200 lines
- `analytics.py`: ~150 lines
- `ui_sections.py`: ~200 lines

---

#### Phase 1-5: app.py 정리 (우선순위: 낮음)

**목표:** 진단 기능 분리

**단계:**
1. `src/diagnostics/` 폴더 생성
2. `supabase_diagnosis.py` 생성 → 진단 함수 이동
3. `app.py`는 라우팅만 남기기

**예상 결과:**
- `app.py`: ~200 lines
- `src/diagnostics/supabase_diagnosis.py`: ~300 lines

---

## 5. 리팩토링 원칙

1. **기능 변경 금지**: 기존 동작 100% 유지
2. **점진적 분리**: 한 번에 하나의 파일만 리팩토링
3. **테스트 우선**: 각 단계마다 동작 확인
4. **의존성 최소화**: 새 모듈 간 순환 참조 방지
5. **네이밍 일관성**: `render_*`, `load_*`, `compute_*` 등 명명 규칙 유지

---

## 6. 다음 단계

1. Phase 1-1부터 시작 (settlement_actual.py)
2. 각 단계 완료 후 커밋
3. 다음 단계 진행 전 충분한 테스트
4. 모든 Phase 완료 후 전체 코드베이스 재분석
