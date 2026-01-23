# PHASE 10 / STEP 10-7A: "오늘의 전략 카드" + 원인→액션 매핑 엔진 (MVP) 완료

## 작업 개요
매출 하락 신호를 감지하고 "오늘 할 일 1개(미션 1개)"로 자동 변환하는 엔진 구현.
HOME / 가게 설계 센터 / 매출 하락 원인 찾기 결과 화면에 재사용 가능한 전략 카드 제공.

---

## 생성/수정된 파일 목록

### 1. 공통 컴포넌트 (신규)
- **`ui_pages/common/__init__.py`** (신규)
- **`ui_pages/common/today_strategy_card.py`** (신규)
  - `render_today_strategy_card(strategy: dict, location: str)` - 전략 카드 렌더링
  - `_render_data_insufficient_card()` - 데이터 부족 시 입력 유도 카드

### 2. 엔진 함수 (신규)
- **`ui_pages/analysis/__init__.py`** (신규)
- **`ui_pages/analysis/strategy_engine.py`** (신규)
  - `get_sales_drop_signals(store_id, ref_date, window_days)` - 매출 하락 신호 수집
  - `_get_top_menu_changes(...)` - 상위메뉴 변화 분석
  - `classify_cause_type(signals)` - 원인 타입 분류 (6개)
  - `build_strategy_card(cause, signals, store_id)` - 원인 → 전략 카드 변환
  - `pick_primary_strategy(store_id, ref_date, window_days)` - 최종 전략 선택

### 3. 적용 위치 (수정)
- **`ui_pages/home/home_page.py`** (수정)
  - ZONE 2(코치 판결) 아래에 "오늘의 전략 카드" 추가
- **`ui_pages/design_lab/design_center.py`** (수정)
  - ZONE C(코치 1차 판결) 아래에 "오늘의 전략 카드" 추가
- **`ui_pages/diagnostics/sales_drop_oneclick.py`** (수정)
  - STEP 3 결과 하단에 "오늘의 전략 카드" 추가

### 4. 문서 (신규)
- **`docs/PHASE10_STEP10_7A_TodayStrategy.md`** (신규)
  - 원인 타입 정의, 매핑표, 세션 컨텍스트 정의 포함

---

## 핵심 구현 내용

### 1. 원인 타입 정의 (6개, 룰 기반)

1. **유입 감소형**: 네이버방문자 -10% 이상
2. **객단가 하락형**: 객단가 -8% 이상 & 네이버방문자 변화 작음
3. **판매량 하락형**: 판매량 -10% 이상
4. **주력메뉴 붕괴형**: Top1~Top3 중 1개 이상 -20% 이상
5. **원가율 악화형**: 고원가율 메뉴 >=3개 또는 평균 공헌이익 <5000원
6. **구조 리스크형**: 손익분기점 대비 예상매출 <1.05

### 2. 원인 → 전략 카드 매핑

각 원인 타입마다:
- **제목**: 짧고 명령형 (예: "마진 메뉴 1개 가격 시뮬")
- **근거**: 2~3개 bullet (반드시 숫자 포함)
- **CTA**: 버튼 텍스트 + 이동 페이지
- **세션 컨텍스트**: 초기 상태를 잡기 위한 힌트 (필터/선택값)
- **대체 전략**: 최대 2개 (expander에 숨김)

### 3. 공통 컴포넌트

- **카드 UI**: 제목(그라데이션) / 근거 bullet / CTA 버튼
- **데이터 부족 처리**: "입력 유도 카드" 자동 표시
- **대체 전략**: expander("다른 추천 보기")에 배치

### 4. 엔진 함수

- **신호 수집**: best_available + 설계 인사이트 기반
- **원인 분류**: 우선순위 + 신뢰도 기준 정렬
- **전략 생성**: 원인 타입별 매핑 규칙 적용
- **최종 선택**: 최우선 원인 기반 전략 카드 1개 + 대체 2개

---

## 데이터 정책 준수

### SSOT best_available 사용
- ✅ `load_best_available_daily_sales()` 사용
- ✅ `v_daily_sales_items_effective` VIEW 사용
- ✅ 설계 인사이트 재사용 (`get_design_insights()`)

### Graceful Fallback
- 데이터 부족 시 빈 dict 반환
- 공통 컴포넌트에서 "입력 유도 카드" 표시
- 에러 발생 시 앱이 깨지지 않도록 try-except 적용

---

## 성능 최적화

### 캐시 활용
- `get_sales_drop_signals()`: `@st.cache_data(ttl=300)` (5분)
- `_get_top_menu_changes()`: `@st.cache_data(ttl=300)` (5분)
- store_id/ref_date/window_days 키 기반 캐싱

---

## 적용 위치

### 1. HOME v2
- **위치**: ZONE 2(코치 판결) 아래
- **기간**: 14일 (기본값)
- **location**: "home"

### 2. 가게 설계 센터
- **위치**: ZONE C(코치 1차 판결) 아래
- **기간**: 14일 (기본값)
- **location**: "design_center"

### 3. 매출 하락 원인 찾기 결과
- **위치**: STEP 3 결과 하단
- **기간**: 사용자 선택 기간 (7/14/30일)
- **location**: "sales_drop_flow"

---

## 회귀 테스트 체크리스트

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

## 주의사항

1. **세션 컨텍스트**: 각 페이지에서 컨텍스트 변수를 읽어서 초기 상태를 설정해야 함 (10-7A에서는 세팅만)
2. **캐시 무효화**: 매출 데이터 입력 후 자동 TTL(5분) 또는 수동 clear 필요
3. **성능**: 첫 로드 시 약간의 지연 가능 (캐시 적용 후 개선)

---

## 완료일
2026-01-24
