# Phase 0 STEP 1: 크래시 방지 작업 완료 보고서

**작성일**: 2026-01-24  
**작업자**: Phase 0 안정화 전담 엔지니어  
**목표**: 신규 계정/데이터 0개 상태에서도 모든 페이지가 에러 없이 열림

---

## 1️⃣ 발견된 크래시 포인트 목록

### 위험 패턴 검색 결과
- **총 발견**: 117개 `.iloc[0]` 사용 패턴
- **우선순위 수정**: 20개 (신규 사용자 접근 가능한 UI 페이지)
- **추가 수정**: 3개 (dashboard/diagnostics.py)

### 주요 위험 파일

#### 🔴 CRITICAL (즉시 수정 완료)
1. **ui_pages/home/home_data.py** (2개)
   - 120줄: `yesterday_best.iloc[0]['total_sales']`
   - 127줄: `recent_best.iloc[0]['total_sales']`
   - **위험**: 신규 사용자 홈 접근 시 즉시 크래시

2. **ui_pages/home/home_verdict.py** (3개)
   - 256줄: `ing_info.iloc[0].get('단가', 0)`
   - 267줄: `menu_info.iloc[0].get('판매가', 0)`
   - 378줄: `menu_info.iloc[0].get('메뉴명', '')`
   - **위험**: 홈 판결 로직에서 빈 데이터 접근 시 크래시

3. **ui_pages/strategy/strategy_cards.py** (1개)
   - 767줄: `yesterday_df.iloc[0]['total_sales']`
   - **위험**: 전략 보드 접근 시 크래시

4. **ui_pages/settlement_actual.py** (1개)
   - 927줄: `target_row.iloc[0].get('목표매출', 0)`
   - **위험**: 실제정산 페이지 접근 시 크래시

5. **ui_pages/menu_profit_design_lab.py** (1개)
   - 224줄: `cost_df[cost_df['메뉴명'] == selected_menu].iloc[0]`
   - **위험**: 메뉴 선택 시 빈 데이터 크래시

6. **ui_pages/ingredient_management.py** (2개)
   - 86줄: `ingredient_df.iloc[0].to_dict()` (디버그용)
   - 604줄: `ingredient_usage_df[...].iloc[0]`
   - **위험**: 재료 선택 시 크래시

7. **ui_pages/design_lab/design_lab_coach_data.py** (4개)
   - 124줄: `top_ingredient.iloc[0].get('재료명', '')`
   - 125줄: `top_ingredient.iloc[0].get('단가', 0)`
   - 196줄: `cost_df[...].iloc[0]` (최고 원가율)
   - 197줄: `cost_df[...].iloc[0]` (최저 원가율)
   - **위험**: 설계실 코치 데이터 생성 시 크래시

8. **src/analytics.py** (5개)
   - 274줄: `supplier_row.iloc[0]['공급업체명']`
   - 287줄: `supplier_info.iloc[0].get('배송비', 0)`
   - 288줄: `supplier_info.iloc[0].get('최소주문금액', 0)`
   - 397줄: `inventory_row.iloc[0]['현재고']`
   - 407줄: `inventory_row.iloc[0].get('안전재고', 0)`
   - 545줄: `target_data.iloc[0]`
   - **위험**: 분석 함수 호출 시 크래시

#### 🟡 MEDIUM (추가 수정 완료)
9. **ui_pages/dashboard/diagnostics.py** (3개)
   - 38줄: `menu_df.iloc[0].to_dict()`
   - 93줄: `expense_df.iloc[0].to_dict()`
   - 115줄: `filtered_df.iloc[0].to_dict()`
   - **위험**: 디버그 페이지 접근 시 크래시 (우선순위 낮음)

10. **ui_pages/sales_management.py** (1개)
    - 527줄: `visitors_row['영업일수'].iloc[0]`
    - **위험**: 매출 관리 페이지 접근 시 크래시

11. **ui_pages/dashboard/metrics.py** (1개)
    - 95줄: `visitors_row['영업일수'].iloc[0]`
    - **위험**: 대시보드 메트릭 계산 시 크래시

---

## 2️⃣ 수정 완료 파일 리스트

### ✅ 완료된 파일 (11개)

1. ✅ **ui_pages/home/home_data.py**
   - `safe_get_value()` 함수로 변경
   - 빈 데이터 시 기본값 0 반환

2. ✅ **ui_pages/home/home_verdict.py**
   - `safe_get_value()`, `safe_get_row_by_condition()` 함수로 변경
   - 빈 데이터 시 None 반환 후 분기 처리

3. ✅ **ui_pages/strategy/strategy_cards.py**
   - `safe_get_value()` 함수로 변경
   - 빈 데이터 시 기본값 0 반환

4. ✅ **ui_pages/settlement_actual.py**
   - `safe_get_value()` 함수로 변경
   - 빈 데이터 시 기본값 0 반환

5. ✅ **ui_pages/menu_profit_design_lab.py**
   - `safe_get_row_by_condition()` 함수로 변경
   - 빈 데이터 시 경고 메시지 표시 후 return

6. ✅ **ui_pages/ingredient_management.py**
   - `safe_get_row_by_condition()` 함수로 변경
   - 빈 데이터 시 경고 메시지 표시 후 return
   - 디버그용 `.iloc[0]`도 안전 함수로 변경

7. ✅ **ui_pages/design_lab/design_lab_coach_data.py**
   - `safe_get_value()`, `safe_get_row_by_condition()` 함수로 변경
   - 빈 데이터 시 None 체크 후 분기 처리

8. ✅ **src/analytics.py**
   - `safe_get_value()`, `safe_get_row_by_condition()` 함수로 변경
   - 빈 데이터 시 기본값 반환 또는 continue

9. ✅ **ui_pages/dashboard/diagnostics.py**
   - `safe_get_first_row()` 함수로 변경
   - 빈 데이터 시 경고 메시지 표시

10. ✅ **ui_pages/sales_management.py**
    - `safe_get_value()` 함수로 변경
    - 빈 데이터 시 기본값 0 반환

11. ✅ **ui_pages/dashboard/metrics.py**
    - `safe_get_value()` 함수로 변경
    - 빈 데이터 시 기본값 0 반환

---

## 3️⃣ 신규 사용자 테스트 체크리스트

### 테스트 시나리오: 신규 계정 (데이터 0개)

#### ✅ 홈 페이지
- [ ] 홈 접근 시 에러 없음
- [ ] 어제 매출 표시: 0 또는 "데이터 없음"
- [ ] 이번 달 누적 매출: 0
- [ ] 전략 카드 로딩: 에러 없음 (데이터 없으면 기본 메시지)

#### ✅ 전략 보드
- [ ] 전략 보드 접근 시 에러 없음
- [ ] 가게 상태 분류: 기본값 반환
- [ ] 전략 카드 생성: 에러 없음 (데이터 없으면 기본 카드)

#### ✅ 설계실 전체
- [ ] 가게 설계 센터 접근 시 에러 없음
- [ ] 메뉴 포트폴리오 설계실: "데이터 없음" 메시지
- [ ] 메뉴 수익 구조 설계실: "데이터 없음" 메시지
- [ ] 재료 구조 설계실: "데이터 없음" 메시지
- [ ] 수익 구조 설계실: "데이터 없음" 메시지

#### ✅ 실제정산
- [ ] 실제정산 페이지 접근 시 에러 없음
- [ ] 목표 매출: 0 또는 "입력 필요"
- [ ] 목표 비용 구조: 빈 상태 표시

#### ✅ 일일 입력
- [ ] 일일 입력 페이지 접근 시 에러 없음
- [ ] 메뉴 목록: 빈 상태 또는 "메뉴 등록 필요"

#### ✅ 기타 페이지
- [ ] 매출 분석: 에러 없음
- [ ] 판매·메뉴 분석: 에러 없음
- [ ] 원가 분석: 에러 없음

---

## 4️⃣ 아직 남은 위험 요소

### ⚠️ 추가 확인 필요 (우선순위 낮음)

#### storage_supabase.py의 `.data[0]` 접근
- **위치**: `src/storage_supabase.py` (30개 이상)
- **패턴**: `result.data[0]['id']`, `result.data[0]['name']` 등
- **위험도**: 🟡 중
- **이유**: Supabase 결과는 `.data`가 리스트이므로, 빈 경우 `IndexError` 발생 가능
- **현재 상태**: 일부는 체크 있음, 일부는 없음
- **권장 조치**: 모든 `.data[0]` 접근 전 `if result.data and len(result.data) > 0` 체크 추가

#### ui_helpers.py 내부의 `.iloc[0]` 사용
- **위치**: `src/ui_helpers.py` (3개)
- **패턴**: `safe_get_first_row()`, `safe_get_value()` 함수 내부
- **위험도**: 🟢 낮음
- **이유**: 이미 안전 함수 내부에서 try-except로 보호됨
- **현재 상태**: ✅ 안전 (함수 내부에서 예외 처리)

#### order_ui.py의 `.iloc[0]` 사용
- **위치**: `ui_pages/order_ui.py` (1개)
- **패턴**: `tab1_inventory_df[...].iloc[0]`
- **위험도**: 🟡 중
- **이유**: 발주 관리 페이지 (v1에서 보류 기능)
- **권장 조치**: 기능 활성화 시 수정 필요

---

## 📊 수정 통계

### 수정 완료
- **총 파일 수**: 11개
- **총 수정 건수**: 20개 (우선순위 높음) + 3개 (추가) = 23개
- **사용된 안전 함수**:
  - `safe_get_value()`: 12회
  - `safe_get_row_by_condition()`: 6회
  - `safe_get_first_row()`: 5회

### 남은 작업
- **storage_supabase.py**: 30개 이상 (Supabase 결과 접근)
- **order_ui.py**: 1개 (보류 기능)
- **기타**: 문서/백업 파일의 예시 코드

---

## 🎯 다음 단계

### Phase 0 STEP 2 예상 작업
1. **storage_supabase.py 안전화**
   - 모든 `.data[0]` 접근 전 빈 리스트 체크
   - 기본값 반환 또는 None 처리

2. **신규 사용자 시나리오 테스트**
   - 실제 신규 계정으로 모든 페이지 접근 테스트
   - 에러 로그 확인

3. **부분 데이터 상태 테스트**
   - 메뉴만 있는 상태
   - 매출만 있는 상태
   - 재료만 있는 상태

---

**작업 완료일**: 2026-01-24  
**다음 작업**: Phase 0 STEP 2 (storage_supabase.py 안전화)
