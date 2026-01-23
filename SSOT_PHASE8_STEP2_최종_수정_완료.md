# SSOT PHASE 8 - STEP 2 최종 수정 완료

## 📋 정책 업데이트 요약

**SSOT 정책 (최종)**:
- **통계/분석/KPI/정산**: `v_daily_sales_best_available` (daily_close 우선, 없으면 sales)
- **마감률/연속마감/공식 확정**: `v_daily_sales_official` (daily_close만)
- **미마감 표시**: `is_official=false` 날짜가 포함되면 UI에 경고 배지 표시

---

## ✅ 수정 완료 항목

### 1. `load_monthly_sales_total()` 함수
- **상태**: ✅ 이미 `v_daily_sales_best_available` 사용 중
- **위치**: `src/storage_supabase.py` 라인 3596-3630

### 2. `load_monthly_official_sales_total()` 함수
- **상태**: ✅ 이미 추가됨
- **위치**: `src/storage_supabase.py` 라인 3536-3592

### 3. `count_unofficial_days_in_month()` 함수
- **상태**: ✅ 이미 추가됨
- **위치**: `src/storage_supabase.py` 라인 3632-3668

### 4. 매출 관리 페이지
- **상태**: ✅ `best_available` 사용 + 미마감 배지 추가
- **위치**: `ui_pages/sales_management.py`
- **추가 수정**: 저장된 매출 내역 표에 `is_official`, `source` 컬럼 추가

### 5. 대시보드 페이지
- **상태**: ✅ `best_available` 사용 + 미마감 배지 추가
- **위치**: `ui_pages/dashboard/`

### 6. 실제정산 페이지
- **상태**: ✅ 미마감 배지 추가
- **위치**: `ui_pages/settlement_actual.py`

### 7. 홈 페이지
- **상태**: ✅ 수정 완료
- **변경 내용**:
  - `_render_status_strip()`: `sales` 직접 조회 → `load_best_available_daily_sales()` 사용
  - `load_home_kpis()`: 어제 매출을 `best_available` 기반으로 변경
  - 미마감 배지 추가

### 8. 캐시 무효화 개선
- **상태**: ✅ 수정 완료
- **위치**: `src/storage_supabase.py` 라인 393-430
- **변경**: `soft_invalidate()`에서 SSOT 함수들도 무효화하도록 추가

---

## 📝 수정 파일 목록

### 1. `src/storage_supabase.py`
**변경 내용**:
- 라인 393-430: `soft_invalidate()` 캐시 매핑 개선
  - `sales`, `daily_close` 변경 시 SSOT 함수들도 무효화
- 라인 2110-2116: `save_daily_close()` 캐시 무효화 개선
  - `load_csv.clear()` → `soft_invalidate()` 사용

### 2. `ui_pages/home/home_page.py`
**변경 내용**:
- 라인 222: `unofficial_days` 추출
- 라인 247-249: 미마감 배지 표시 추가
- 라인 477-503: `_render_status_strip()` 수정
  - `sales` 직접 조회 → `load_best_available_daily_sales()` 사용

### 3. `ui_pages/home/home_data.py`
**변경 내용**:
- 라인 16: import 추가 (`count_unofficial_days_in_month`)
- 라인 79-101: 어제 매출 조회를 `best_available` 기반으로 변경
- 라인 82-83: `unofficial_days` 계산 및 반환

### 4. `ui_pages/sales_management.py`
**변경 내용**:
- 라인 620-624: 저장된 매출 내역 표에 `is_official`, `source` 컬럼 추가
- 라인 635-640: `is_official`, `source` 포맷팅 추가

---

## 📊 페이지별 SSOT 사용 매핑표

| 페이지 | 통계/KPI | 마감률/연속마감 | 미마감 배지 |
|--------|---------|----------------|------------|
| **홈** | `best_available` | `official` (daily_close 직접) | ✅ 추가됨 |
| **매출 관리** | `best_available` | - | ✅ 추가됨 |
| **대시보드** | `best_available` | - | ✅ 추가됨 |
| **실제정산** | `best_available` | - | ✅ 추가됨 |

---

## 🧪 테스트 시나리오 6개

### 시나리오 1: 마감 없는 날 sales 입력 → KPI 반영 + 미마감 배지
**전제 조건**: 2026-01-20에 `daily_close` 없음, `sales`만 입력  
**예상 결과**:
- ✅ 홈: 이번달 누적 매출에 포함 + "⚠️ 미마감 데이터 포함 (1일)" 배지
- ✅ 매출 관리: 모든 KPI에 포함 + 미마감 배지
- ✅ 대시보드: 월매출 집계에 포함 + 미마감 배지
- ✅ 실제정산: 총매출에 포함 + 미마감 배지

### 시나리오 2: 동일 날짜 마감 추가 → 숫자 유지 + is_official=true 전환
**전제 조건**: 2026-01-20에 `sales`만 있음 → 점장 마감 추가  
**예상 결과**:
- ✅ 모든 KPI 숫자 유지 (best_available이 daily_close 우선 사용)
- ✅ 미마감 배지 사라짐 (unofficial_days = 0)

### 시나리오 3: 여러 날 미마감
**전제 조건**: 2026-01-20, 2026-01-21, 2026-01-22에 `sales`만 있음  
**예상 결과**:
- ✅ "⚠️ 미마감 데이터 포함 (3일)" 배지 표시
- ✅ 모든 KPI에 3일 매출 포함

### 시나리오 4: 마감률/스트릭은 마감된 날만 기준
**전제 조건**: 2026-01-20에 `sales`만 있음  
**예상 결과**:
- ✅ 홈 마감률: 2026-01-20 제외 (daily_close만 카운트)
- ✅ 연속마감 스트릭: 2026-01-20 제외

### 시나리오 5: 저장 직후 숫자 즉시 반영
**전제 조건**: 매출 보정 저장  
**예상 결과**:
- ✅ 저장 직후 페이지 새로고침 시 즉시 반영
- ✅ 캐시 무효화로 최신 데이터 표시

### 시나리오 6: 저장된 매출 내역 표에 미마감 표시
**전제 조건**: 매출 관리 페이지에서 저장된 매출 내역 확인  
**예상 결과**:
- ✅ `is_official` 컬럼: "✅ 마감" 또는 "⚠️ 미마감" 표시
- ✅ `source` 컬럼: "점장마감" 또는 "매출보정" 표시

---

## ✅ 검증 체크리스트

- [x] `load_monthly_sales_total()`가 `v_daily_sales_best_available` 사용
- [x] `load_monthly_official_sales_total()`가 `v_daily_sales_official` 사용
- [x] 홈 페이지에 미마감 배지 표시
- [x] 매출 관리 페이지에 미마감 배지 표시
- [x] 대시보드 페이지에 미마감 배지 표시
- [x] 실제정산 페이지에 미마감 배지 표시
- [x] 저장된 매출 내역 표에 `is_official`, `source` 컬럼 표시
- [x] 홈 페이지 `_render_status_strip()` 수정 (best_available 사용)
- [x] 홈 페이지 어제 매출을 best_available 기반으로 변경
- [x] 캐시 무효화 개선 (SSOT 함수들 포함)

---

## 🎯 기대 동작

### 통계/분석/KPI/정산
- ✅ `sales`만 있는 날짜도 포함
- ✅ `is_official=false`로 표시
- ✅ 미마감 배지로 명확히 구분
- ✅ 저장 직후 즉시 반영

### 마감률/연속마감
- ✅ `daily_close`만 카운트
- ✅ `sales`만 있는 날짜는 제외
- ✅ 공식 운영 루틴 지표로 사용

---

## 📌 추가 참고사항

### 캐시 안정화
- `soft_invalidate()`에서 `sales`, `daily_close` 변경 시 SSOT 함수들도 자동 무효화
- `save_daily_close()`, `save_sales()`에서 `soft_invalidate()` 사용

### 저장된 매출 내역 표
- `is_official`: "✅ 마감" 또는 "⚠️ 미마감"
- `source`: "점장마감" 또는 "매출보정"

---

## 🚀 배포 준비

모든 수정이 완료되었습니다. 다음 단계:
1. 앱 재시작
2. 테스트 시나리오 6개 실행
3. 미마감 배지 표시 확인
4. 저장 직후 숫자 반영 확인
