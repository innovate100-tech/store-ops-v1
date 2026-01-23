# SSOT 페이지 감사 결과

## 📋 감사 개요

**감사 일자**: 2026-01-23  
**대상 페이지**: 4개 핵심 페이지  
**SSOT 정책**: `daily_close` = 공식 SSOT, `sales` = 보조 입력 채널

---

## 📊 페이지별 SSOT 적합도 표

| 페이지 | 적합도 | 공식 매출 소스 | sales-only 섞임 | best_available 사용 | 수정 필요 |
|--------|--------|---------------|-----------------|---------------------|----------|
| **홈 (home_page)** | 🟡 | `daily_close` 직접 조회 | ⚠️ 가능성 있음 | ❌ 미사용 | 권장 |
| **매출 관리 (sales_management)** | 🔴 | `sales` 테이블 직접 | ✅ **있음** | ❌ 미사용 | **필수** |
| **대시보드 (dashboard)** | 🔴 | `load_monthly_sales_total` → `sales` 직접 | ✅ **있음** | ❌ 미사용 | **필수** |
| **실제정산 (settlement_actual)** | 🔴 | `load_monthly_sales_total` → `sales` 직접 | ✅ **있음** | ❌ 미사용 | **필수** |

---

## 1️⃣ 홈 페이지 (`ui_pages/home/home_page.py` + `home_data.py`)

### A. 공식 매출 집계 소스
- **현재**: `daily_close` 테이블 직접 조회
- **사용 위치**:
  - `home_data.py::load_home_kpis()`: `daily_close`에서 `yesterday_sales` 조회 (라인 86-101)
  - `home_data.py::get_monthly_close_stats()`: `daily_close`에서 마감 통계 조회 (라인 31-33)
  - `home_page.py::_render_status_strip()`: `sales` 테이블 직접 조회 (라인 487-493) ⚠️

### B. sales-only 날짜가 공식 KPI/차트에 섞일 가능성
- **있음** ⚠️
- **위치**: `home_page.py::_render_status_strip()` (라인 487-493)
  ```python
  recent_sales = supabase.table("sales").select("total_sales")...
  month_sales_list = supabase.table("sales").select("total_sales")...
  ```
- **영향**: 최근 7일 평균 vs 이번 달 평균 비교에서 `sales`만 있는 날짜가 포함됨

### C. best_available 사용 여부
- ❌ 미사용
- **권장**: 마감 누락 감지용으로 `v_daily_sales_best_available` 사용 고려

### D. 필요한 수정 항목

#### (권장) `_render_status_strip()` 함수 수정
- **위치**: `ui_pages/home/home_page.py` 라인 487-493
- **현재**: `sales` 테이블 직접 조회
- **수정**: `v_daily_sales_official` 또는 `load_official_daily_sales()` 사용
- **우선순위**: 중간 (홈 페이지는 참고용이므로)

---

## 2️⃣ 매출 관리 페이지 (`ui_pages/sales_management.py`)

### A. 공식 매출 집계 소스
- **현재**: `sales` 테이블 직접 조회 (`load_csv('sales.csv')`)
- **사용 위치**:
  - 라인 53: `sales_df = load_csv('sales.csv', ...)`
  - 라인 111-116: `month_data['총매출']` 직접 합산 또는 `load_monthly_sales_total()` fallback
  - 라인 224, 241, 257: 전월/작년 동월/주간 비교에서 `merged_df['총매출']` 직접 사용

### B. sales-only 날짜가 공식 KPI/차트에 섞일 가능성
- **있음** ✅ **심각**
- **위치**: 모든 매출 집계 로직
- **영향**: 
  - 이번달 누적 매출 (라인 157)
  - 전월 대비 비교 (라인 224)
  - 작년 동월 대비 비교 (라인 241)
  - 주간 비교 (라인 257)
  - 요일별 분석 (라인 291-297)
  - 월별 요약 (라인 496-512)
  - **모든 공식 KPI가 `sales` 테이블 기반**

### C. best_available 사용 여부
- ❌ 미사용
- **권장**: 마감 누락 감지용으로 사용 고려

### D. 필요한 수정 항목

#### (필수) SSOT 위반 수정
- **위치**: `ui_pages/sales_management.py` 전체
- **현재**: `load_csv('sales.csv')` → `sales` 테이블 직접 조회
- **수정**: `load_official_daily_sales()` 또는 `v_daily_sales_official` 사용
- **우선순위**: **최우선** (공식 매출 관리 페이지이므로)

**수정 범위**:
1. 라인 53: `sales_df = load_csv('sales.csv')` → `load_official_daily_sales()` 사용
2. 라인 111-116: `month_data['총매출']` 합산 로직 → official view 기반으로 변경
3. 라인 224, 241, 257: 전월/작년/주간 비교 → official view 기반
4. 라인 291-297: 요일별 분석 → official view 기반
5. 라인 496-512: 월별 요약 → official view 기반

**주의사항**:
- `load_csv('sales.csv')`는 `sales` 테이블을 조회하므로 SSOT 위반
- `load_official_daily_sales()`는 `v_daily_sales_official` 뷰를 조회하므로 SSOT 준수

---

## 3️⃣ 대시보드 페이지 (`ui_pages/dashboard/dashboard.py` + `data_loaders.py` + `metrics.py`)

### A. 공식 매출 집계 소스
- **현재**: `load_monthly_sales_total()` 함수 사용
- **사용 위치**:
  - `metrics.py::compute_monthly_summary()`: 라인 81에서 `load_monthly_sales_total()` 호출
  - `metrics.py::_compute_dashboard_metrics()`: 라인 277에서 `load_monthly_sales_total()` 호출
  - `data_loaders.py::_load_dashboard_data()`: 라인 14에서 `load_csv('sales.csv')` 사용 ⚠️

### B. sales-only 날짜가 공식 KPI/차트에 섞일 가능성
- **있음** ✅ **심각**
- **위치**: 
  1. `metrics.py::_compute_dashboard_metrics()` (라인 277): `load_monthly_sales_total()` → `sales` 직접 조회
  2. `metrics.py::compute_monthly_summary()` (라인 81): `load_monthly_sales_total()` → `sales` 직접 조회
  3. `data_loaders.py::_load_dashboard_data()` (라인 14): `load_csv('sales.csv')` → `sales` 직접 조회
- **영향**: 
  - 월매출 집계가 `sales` 테이블 기반 (라인 277, 81)
  - `sales_df`가 차트/표시에 사용될 경우 `sales`만 있는 날짜 포함

### C. best_available 사용 여부
- ❌ 미사용
- **권장**: 마감 누락 감지용으로 사용 고려

### D. 필요한 수정 항목

#### (필수) `load_monthly_sales_total()` 함수 수정
- **위치**: `src/storage_supabase.py` 라인 3536-3585
- **현재**: `sales` 테이블 직접 조회
- **수정**: `v_daily_sales_official` 뷰 사용
- **우선순위**: **최우선** (대시보드/실제정산/매출관리 모두 사용)

**수정 방법**:
```python
# 변경 전
result = supabase.table("sales")\
    .select("total_sales")\
    .eq("store_id", store_id)\
    .gte("date", start_date_str)\
    .lt("date", end_date_str)\
    .execute()

# 변경 후
result = supabase.table("v_daily_sales_official")\
    .select("total_sales")\
    .eq("store_id", store_id)\
    .gte("date", start_date_str)\
    .lt("date", end_date_str)\
    .execute()
```

#### (권장) `_load_dashboard_data()` 함수 수정
- **위치**: `ui_pages/dashboard/data_loaders.py` 라인 14
- **현재**: `load_csv('sales.csv')` 사용
- **수정**: `load_official_daily_sales()` 사용
- **우선순위**: 중간

---

## 4️⃣ 실제정산 페이지 (`ui_pages/settlement_actual.py`)

### A. 공식 매출 집계 소스
- **현재**: `load_monthly_sales_total()` 함수 사용
- **사용 위치**:
  - 라인 275, 292, 330: `load_monthly_sales_total()` 호출
  - 라인 551: `sales` 테이블 직접 조회 (DEV 모드 진단용) ⚠️

### B. sales-only 날짜가 공식 KPI/차트에 섞일 가능성
- **있음** ✅ **심각**
- **위치**: 
  1. 라인 275, 292, 330: `load_monthly_sales_total()` → `sales` 직접 조회
  2. 라인 551: `sales` 테이블 직접 조회 (DEV 모드 진단용)
- **영향**: 
  - 총매출 자동 불러오기가 `sales` 테이블 기반 (라인 275, 292, 330)
  - **실제정산의 핵심 KPI가 SSOT 위반**

### C. best_available 사용 여부
- ❌ 미사용
- **권장**: 마감 누락 감지용으로 사용 고려

### D. 필요한 수정 항목

#### (필수) `load_monthly_sales_total()` 함수 수정
- **위치**: `src/storage_supabase.py` 라인 3536-3585
- **현재**: `sales` 테이블 직접 조회
- **수정**: `v_daily_sales_official` 뷰 사용
- **우선순위**: **최우선** (실제정산의 핵심 함수)

**참고**: `load_monthly_sales_total()` 수정 시 실제정산 페이지는 자동으로 SSOT 준수됨

#### (선택) DEV 모드 진단 코드 수정
- **위치**: `ui_pages/settlement_actual.py` 라인 551
- **현재**: `sales` 테이블 직접 조회 (DEV 모드 진단용)
- **수정**: `v_daily_sales_official` 사용 (선택사항)
- **우선순위**: 낮음 (DEV 모드 진단용이므로)

---

## 🔍 핵심 함수 확인: `load_monthly_sales_total()`

### 현재 구현 확인 결과
- **위치**: `src/storage_supabase.py` 라인 3536-3585
- **현재 상태**: ❌ **`sales` 테이블 직접 조회** (SSOT 위반)
- **코드**:
  ```python
  result = supabase.table("sales")\
      .select("total_sales")\
      .eq("store_id", store_id)\
      .gte("date", start_date_str)\
      .lt("date", end_date_str)\
      .execute()
  ```

### 영향 범위
- ❌ **대시보드**: `load_monthly_sales_total()` 사용 → SSOT 위반
- ❌ **실제정산**: `load_monthly_sales_total()` 사용 → SSOT 위반
- ❌ **매출 관리**: `load_monthly_sales_total()` fallback 사용 → SSOT 위반

### 수정 필요
- **필수**: `load_monthly_sales_total()` 함수를 `v_daily_sales_official` 뷰 사용하도록 수정

---

## 📝 수정 우선순위 요약

### 🔴 필수 수정 (SSOT 위반)
1. **`load_monthly_sales_total()` 함수** (`src/storage_supabase.py` 라인 3536-3585)
   - `sales` 테이블 직접 조회 → `v_daily_sales_official` 뷰 사용
   - 영향 범위: 대시보드, 실제정산, 매출관리 (fallback)
   - **최우선**: 모든 페이지의 기반 함수

2. **매출 관리 페이지** (`ui_pages/sales_management.py`)
   - 모든 매출 집계를 `load_official_daily_sales()` 또는 `v_daily_sales_official`로 변경
   - 영향 범위: 전체 페이지

### 🟡 권장 수정 (구조 개선)
2. **홈 페이지** (`ui_pages/home/home_page.py`)
   - `_render_status_strip()` 함수에서 `sales` → `v_daily_sales_official` 변경
   - 영향 범위: 최근 7일 평균 비교 로직

3. **대시보드** (`ui_pages/dashboard/data_loaders.py`)
   - `_load_dashboard_data()`에서 `load_csv('sales.csv')` → `load_official_daily_sales()` 변경
   - 영향 범위: `sales_df` 사용 부분

### 🟢 선택 수정 (UX 경고 추가)
4. **모든 페이지**: 마감 누락 감지용으로 `v_daily_sales_best_available` 사용 고려

---

## ✅ 수정 후 기대 동작

### 매출 관리 페이지
- ✅ 공식 KPI는 `daily_close` 기반만 표시
- ✅ `sales`만 있는 날짜는 공식 집계에서 제외
- ✅ 마감 누락 날짜는 별도 경고 표시 가능

### 홈 페이지
- ✅ 최근 7일 평균 비교가 공식 매출만 사용
- ✅ 마감 누락 날짜 감지 가능

### 대시보드
- ✅ 모든 차트/집계가 공식 매출만 사용
- ✅ 마감 누락 날짜 감지 가능

### 실제정산
- ✅ 월매출이 공식 매출만 사용 (이미 `load_monthly_sales_total()` 사용 중)

---

## 🔧 다음 단계

1. **`load_monthly_sales_total()` 함수 수정 (최우선)**
   - `src/storage_supabase.py` 라인 3570-3575
   - `supabase.table("sales")` → `supabase.table("v_daily_sales_official")`
   - 영향: 대시보드, 실제정산, 매출관리 자동 수정됨

2. **매출 관리 페이지 수정 (필수)**
   - `ui_pages/sales_management.py` 라인 53
   - `load_csv('sales.csv')` → `load_official_daily_sales()`
   - 모든 집계 로직 변경 (라인 111-116, 224, 241, 257, 291-297, 496-512)

3. **홈 페이지 수정 (권장)**
   - `ui_pages/home/home_page.py` 라인 487-493
   - `sales` 직접 조회 → `v_daily_sales_official` 사용

4. **대시보드 데이터 로더 수정 (권장)**
   - `ui_pages/dashboard/data_loaders.py` 라인 14
   - `load_csv('sales.csv')` → `load_official_daily_sales()`

5. **마감 누락 감지 기능 추가 (선택)**
   - `v_daily_sales_best_available` 사용하여 마감 누락 날짜 표시
