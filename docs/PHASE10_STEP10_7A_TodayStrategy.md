# PHASE 10 / STEP 10-7A: "오늘의 전략 카드" + 원인→액션 매핑 엔진 (MVP)

## 개요
매출 하락 신호를 감지하고 "오늘 할 일 1개(미션 1개)"로 자동 변환하는 엔진.
HOME / 가게 설계 센터 / 매출 하락 원인 찾기 결과 화면에 재사용 가능한 전략 카드 제공.

---

## 원인 타입 정의 (6개)

### 1. 유입 감소형
- **조건**: 네이버방문자 14일 평균이 이전 14일 대비 -10% 이상
- **우선순위**: 1
- **신뢰도**: abs(visitors_change_pct) / 20.0 (최대 1.0)

### 2. 객단가 하락형
- **조건**: 객단가 -8% 이상 & 네이버방문자 변화가 작음(-5% 이내)
- **우선순위**: 2
- **신뢰도**: abs(avgp_change_pct) / 15.0 (최대 1.0)

### 3. 판매량 하락형
- **조건**: 판매량(아이템합) -10% 이상
- **우선순위**: 3
- **신뢰도**: abs(qty_change_pct) / 20.0 (최대 1.0)

### 4. 주력메뉴 붕괴형
- **조건**: Top1~Top3 중 1개 이상 매출 -20% 이상
- **우선순위**: 4
- **신뢰도**: severe_drop_count / 3.0 (최대 1.0)

### 5. 원가율 악화형
- **조건**: 고원가율(>=35%) 메뉴 수 증가 또는 평균 공헌이익 < 5000원
- **우선순위**: 5
- **신뢰도**: high_cogs_count / 5.0 (최대 1.0)

### 6. 구조 리스크형
- **조건**: 손익분기점 대비 예상매출 < 1.05 (105% 미만)
- **우선순위**: 6
- **신뢰도**: 1.0 - break_even_gap_ratio (break_even_gap < 1.0일 때)

---

## 원인 타입 → 전략 카드 매핑표

| 원인 타입 | 전략 카드 제목 | 근거 (2~3개) | CTA 버튼 | 이동 페이지 | 세션 컨텍스트 |
|---------|------------|------------|---------|----------|------------|
| 유입 감소형 | 포트폴리오 미분류 메뉴 1개 정리 | 네이버방문자 {change_pct}% 감소<br>유인메뉴/대표메뉴 구성 점검 필요 | 메뉴 포트폴리오 설계실 열기 | 메뉴 등록 | `_filter_unclassified: True` |
| 객단가 하락형 | 고원가율 메뉴 1개 가격 시뮬 | 객단가 {change_pct}% 하락<br>가격/마진 구조 점검 필요 | 가격 시뮬레이터 열기 | 메뉴 수익 구조 설계실 | `_filter_high_cogs: True`<br>`_initial_tab_메뉴 수익 구조 설계실: "execute"` |
| 판매량 하락형 | 주력메뉴 판매량 1개 점검 | 총 판매량 {change_pct}% 감소<br>주력메뉴 판매 추이 확인 필요 | 판매·메뉴 분석 열기 | 판매 관리 | `_period_days: 14` |
| 주력메뉴 붕괴형 | {menu_name} 가격/마진 시뮬 | {menu_name} 판매량 {change_pct}% 급감<br>가격/마진 구조 재점검 필요 | 가격 시뮬레이터 열기 | 메뉴 수익 구조 설계실 | `_selected_menu: {menu_name}`<br>`_initial_tab_메뉴 수익 구조 설계실: "execute"` |
| 원가율 악화형 | 고원가율 메뉴 1개 가격 시뮬 | 고원가율 메뉴 {count}개 확인<br>가격 조정 또는 원가 절감 필요 | 가격 시뮬레이터 열기 | 메뉴 수익 구조 설계실 | `_filter_high_cogs: True`<br>`_initial_tab_메뉴 수익 구조 설계실: "execute"` |
| 구조 리스크형 | 손익분기점 시나리오 시뮬 | 손익분기점 대비 {ratio}%<br>고정비/변동비 구조 점검 필요 | 시나리오 시뮬레이터 열기 | 수익 구조 설계실 | `_initial_tab_수익 구조 설계실: "execute"` |

---

## 대체 전략 (Alternatives)

각 원인 타입마다 최대 2개의 대체 전략을 제공:

### 유입 감소형
- **대체 1**: 매출 분석으로 유입 원인 파악 → 매출 관리 (`_period_days: 14`)

### 객단가 하락형
- **대체 1**: 포트폴리오 분류 점검 → 메뉴 등록 (`_initial_tab_메뉴 등록: "execute"`)

### 판매량 하락형
- **대체 1**: 포트폴리오 균형 점검 → 메뉴 등록 (`_initial_tab_메뉴 등록: "execute"`)

### 주력메뉴 붕괴형
- **대체 1**: 판매·메뉴 분석 → 판매 관리 (`_period_days: 14`)

### 원가율 악화형
- **대체 1**: 재료 구조 설계실 → 재료 등록 (`_filter_high_risk: True`, `_initial_tab_재료 등록: "execute"`)

### 구조 리스크형
- **대체 1**: 목표 비용 구조 입력 → 목표 비용구조

---

## 세션 컨텍스트 (초기 상태) 정의

### 메뉴 수익 구조 설계실
- `_filter_high_cogs: True` → 원가율>=35% 필터
- `_selected_menu: {menu_name}` → 특정 메뉴 선택

### 메뉴 포트폴리오 설계실 (메뉴 등록)
- `_filter_unclassified: True` → 미분류만 필터

### 재료 구조 설계실 (재료 등록)
- `_filter_high_risk: True` → 고위험 재료 필터

### 수익 구조 설계실
- `_initial_tab_수익 구조 설계실: "execute"` → 전략 실행 탭 기본 열기

### 매출 분석 / 판매·메뉴 분석
- `_period_days: 14` → 기간 14일 자동 선택

---

## 구현 파일 구조

### 1. 공통 컴포넌트
- **`ui_pages/common/today_strategy_card.py`**
  - `render_today_strategy_card(strategy: dict, location: str)`
  - 데이터 부족 시 입력 유도 카드

### 2. 엔진 함수
- **`ui_pages/analysis/strategy_engine.py`**
  - `get_sales_drop_signals(store_id, ref_date, window_days)` - 신호 수집
  - `classify_cause_type(signals)` - 원인 분류
  - `build_strategy_card(cause, signals, store_id)` - 전략 카드 생성
  - `pick_primary_strategy(store_id, ref_date, window_days)` - 최종 전략 선택

### 3. 적용 위치
- **HOME v2**: `ui_pages/home/home_page.py` - ZONE 2 아래
- **가게 설계 센터**: `ui_pages/design_lab/design_center.py` - ZONE C 아래
- **매출 하락 원인 찾기**: `ui_pages/diagnostics/sales_drop_oneclick.py` - 결과 하단

---

## 데이터 정책

### SSOT best_available 사용
- ✅ `load_best_available_daily_sales()` 사용
- ✅ `v_daily_sales_best_available` VIEW 기반
- ✅ 판매량: `v_daily_sales_items_effective` VIEW 사용

### 설계 인사이트 활용
- ✅ `get_design_insights()` 재사용
- ✅ 원가율/공헌이익, 손익분기점 정보 활용

### Graceful Fallback
- 데이터 부족 시 빈 dict 반환
- 공통 컴포넌트에서 "입력 유도 카드" 표시

---

## 성능 최적화

### 캐시 적용
- `get_sales_drop_signals()`: `@st.cache_data(ttl=300)` (5분)
- `_get_top_menu_changes()`: `@st.cache_data(ttl=300)` (5분)
- store_id/ref_date/window_days 키 기반 캐싱

---

## 체크리스트

### ✅ 데이터 부족 케이스
- [x] 매출 데이터 없을 때 입력 유도 카드 표시
- [x] 판매량/방문자 데이터 없을 때 graceful fallback
- [x] 설계 인사이트 없을 때 기본 전략 제공

### ✅ 정상 케이스
- [x] 원인 타입 6개 정상 분류되는지
- [x] 우선순위 기반 전략 카드 선정되는지
- [x] 근거에 숫자 포함되는지
- [x] CTA 버튼 클릭 시 해당 페이지로 이동하는지
- [x] 세션 컨텍스트 정상 세팅되는지

### ✅ 위험 케이스
- [x] 여러 원인 동시 감지 시 우선순위 정렬되는지
- [x] 대체 전략이 expander에 정상 표시되는지
- [x] 에러 발생 시 앱이 깨지지 않는지

### ✅ 적용 위치
- [x] HOME v2에 전략 카드 노출되는지
- [x] 가게 설계 센터에 전략 카드 노출되는지
- [x] 매출 하락 원인 찾기 결과에 전략 카드 노출되는지

---

## 완료일
2026-01-24
