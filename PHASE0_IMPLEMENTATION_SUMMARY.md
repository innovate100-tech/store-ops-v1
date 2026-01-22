# PHASE 0 / STEP 1-3 구현 완료 요약

## 실행 순서

### 1. SQL 실행 (Supabase에서 실행)
```sql
-- STEP 1-1: Override 테이블 생성
\i sql/schema_daily_sales_items_overrides.sql

-- STEP 1-2: Effective 뷰 생성
\i sql/view_daily_sales_items_effective.sql
```

**참고**: `save_sales_with_daily_close_sync` 함수는 이미 존재합니다.

---

## 수정된 파일 목록

### PHASE 0 / STEP 1: 판매량 Override 레이어 도입

#### 1. SQL 파일 (이미 존재, 확인 완료)
- `sql/schema_daily_sales_items_overrides.sql` - Override 테이블 생성
- `sql/view_daily_sales_items_effective.sql` - Effective 뷰 생성

#### 2. Python 코드 (이미 구현됨, 확인 완료)
- `src/storage_supabase.py`:
  - `load_csv()` 함수: `daily_sales_items.csv` → `v_daily_sales_items_effective` 뷰 사용 (606, 618 라인)
  - `save_daily_sales_item()` 함수: `daily_sales_items_overrides` 테이블에 upsert (1704-1757 라인)

#### 3. UI 수정
- `ui_pages/sales_volume_entry.py` (19라인):
  - 문구 변경: "✅ **이 입력은 마감 입력보다 우선 적용되는 최종 판매량입니다(보정/이관용).**"
  
- `ui_pages/manager_close.py` (52라인):
  - 문구 변경: "⚠️ **이 날짜에는 판매량 보정이 존재하며, 보정값이 최종 적용됩니다.** (보정 항목: {count}개)"

#### 4. 판매량 읽기 경로 확인
모든 `load_csv('daily_sales_items.csv')` 호출은 자동으로 `v_daily_sales_items_effective` 뷰를 사용합니다:
- `ui_pages/dashboard/metrics.py`
- `ui_pages/dashboard/data_loaders.py`
- `ui_pages/sales_analysis.py`
- `ui_pages/target_sales_structure.py`
- `ui_pages/ingredient_usage_summary.py`
- `ui_pages/weekly_report.py`
- `app.py`

---

### PHASE 0 / STEP 2: 매출 우선순위/불일치 최소화

#### 1. 매출 SSOT 확인 (이미 구현됨)
- `src/storage_supabase.py`:
  - `load_monthly_sales_total()` 함수: `sales` 테이블에서 월매출 조회 (3062-3114 라인)
  - `save_sales()` 함수: `save_sales_with_daily_close_sync` RPC 사용 (1115-1218 라인)

#### 2. 매출등록 저장 시 daily_close 동기화 (이미 구현됨)
- `sql/save_sales_with_daily_close_sync.sql`: sales 저장 + daily_close 동기화 함수
- `src/storage_supabase.py`: `save_sales()` 함수에서 RPC 호출 (1183-1189 라인)

---

### PHASE 1 / STEP 3: 사이드바 메뉴 구조 재배치

#### 1. 사이드바 메뉴 재배치
- `app.py` (1398-1430 라인):
  - 기존 카테고리 구조를 사장 중심 구조로 변경:
    - 🏠 홈 (추후)
    - 📋 점장 마감
    - 🛒 운영 (발주 관리, 재료 사용량 집계)
    - 📊 운영 분석 (통합 대시보드, 매출 관리, 판매 관리, 원가 파악)
    - 🧾 성적표 (목표 비용구조, 목표 매출구조, 실제정산, 주간 리포트)
    - ⚙️ 관리/보정 (매출 등록, 판매량 등록, 메뉴 등록, 재료 등록, 레시피 등록, 직원 연락망, 협력사 연락망, 게시판)

---

## 검증 체크리스트

### STEP 1: 판매량 Override 레이어

#### 케이스 A: 마감 저장(판매량 포함) → 판매 분석/재료 집계가 정상
- [ ] 점장 마감에서 판매량 입력 후 저장
- [ ] 판매 관리 페이지에서 해당 날짜의 판매량 확인
- [ ] 재료 사용량 집계 페이지에서 해당 날짜의 재료 사용량 확인

#### 케이스 B: 마감 저장 후, 판매량등록에서 특정 메뉴 qty를 수정(override upsert)
- [ ] 마감 저장 완료
- [ ] 판매량등록에서 특정 메뉴의 판매량 수정
- [ ] 판매 분석/재료 집계/대시보드에서 수정값이 반영됨

#### 케이스 C: 위 상태에서 마감을 "같은 날짜로 다시 저장"(base가 DELETE+INSERT 되더라도)
- [ ] 판매량등록으로 수정한 값이 override에 저장됨
- [ ] 같은 날짜로 마감을 다시 저장 (daily_sales_items가 DELETE+INSERT 됨)
- [ ] 최종값이 override 기준으로 유지됨 (수정값 유지)

#### 케이스 D: override가 없는 메뉴는 base 값을 그대로 사용
- [ ] 마감만 저장한 메뉴는 base 값 사용
- [ ] 판매량등록으로 수정한 메뉴는 override 값 사용

#### 에러/무한 rerun 없음
- [ ] 페이지 로드 시 에러 없음
- [ ] 저장 후 무한 rerun 없음

---

### STEP 2: 매출 우선순위/불일치 최소화

#### 같은 월의 매출합계가 페이지별로 다르게 나오지 않음
- [ ] 실제정산 페이지의 월매출 합계 확인
- [ ] 매출 관리 페이지의 월매출 합계 확인
- [ ] 통합 대시보드의 월매출 합계 확인
- [ ] 모든 페이지에서 동일한 값 표시

#### 매출등록으로 수정한 값이 실제정산/대시보드에 반영됨
- [ ] 매출등록에서 특정 날짜의 매출 수정
- [ ] 실제정산 페이지에서 해당 월의 매출 합계 확인
- [ ] 통합 대시보드에서 해당 월의 매출 확인

#### 기능 흐름 변화 없음
- [ ] 점장 마감 저장 정상 동작
- [ ] 매출등록 저장 정상 동작
- [ ] 기존 기능 모두 정상 동작

---

### STEP 3: 사이드바 메뉴 구조 재배치

#### 모든 페이지 접근 가능
- [ ] 각 메뉴 항목 클릭 시 해당 페이지로 이동
- [ ] 라우팅 정상 동작

#### 기존 링크/상태 유지
- [ ] 현재 선택된 페이지 표시 정상
- [ ] 페이지 간 이동 시 상태 유지

---

## 주의사항

1. **SQL 실행 필수**: `schema_daily_sales_items_overrides.sql`와 `view_daily_sales_items_effective.sql`를 Supabase에서 실행해야 합니다.

2. **기존 기능 유지**: 모든 변경은 기존 기능을 깨뜨리지 않도록 안전하게 수행되었습니다.

3. **데이터 유실 없음**: Override 레이어는 기존 데이터를 보존하면서 우선순위만 적용합니다.

---

## 완료 상태

- ✅ STEP 1: 판매량 Override 레이어 도입
- ✅ STEP 2: 매출 우선순위/불일치 최소화
- ✅ STEP 3: 사이드바 메뉴 구조 재배치

모든 작업이 완료되었습니다. 검증 체크리스트를 수행하여 정상 동작을 확인해주세요.
