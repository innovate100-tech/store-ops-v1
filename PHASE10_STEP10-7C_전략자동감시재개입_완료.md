# PHASE 10 / STEP 10-7C: "전략 → 자동 감시 → 재개입" 루프 완성 (코치 개입 엔진 v1) 완료

## 작업 개요
10-7B의 전략 미션을 완료 후 자동 감시 상태로 전환하고, 숫자 변화를 기반으로 결과를 자동 판정하며, 다음 개입을 자동으로 제안하는 루프 완성.
"분석 도구"가 아닌 **'개입형 숫자 코치'**로 진화.

---

## 생성/수정된 파일 목록

### 1. SQL 스키마 확장 (수정)
- **`sql/phase10_strategy_execution.sql`** (수정)
  - strategy_missions 컬럼 추가: monitor_start_date, evaluation_date, result_type, coach_comment
  - status CHECK 제약 확장: 'monitoring', 'evaluated' 추가
  - strategy_mission_results 테이블 생성 (신규)
  - 인덱스 추가

### 2. 모니터링 엔진 (신규)
- **`src/strategy/__init__.py`** (신규)
- **`src/strategy/strategy_monitor.py`** (신규)
  - `evaluate_mission_effect()` - 미션 효과 자동 평가
  - `_classify_result()` - 결과 타입 분류 및 코치 코멘트 생성

### 3. 재개입 엔진 (신규)
- **`src/strategy/strategy_followup.py`** (신규)
  - `decide_next_intervention()` - 다음 개입 결정

### 4. Storage 함수 확장 (수정)
- **`src/storage_supabase.py`** (수정)
  - `set_mission_status()` - status 확장 (monitoring, evaluated)
  - `save_mission_result()` - 미션 결과 저장
  - `update_mission_evaluation()` - 평가 결과 업데이트
  - `load_mission_result()` - 미션 결과 조회
  - `load_recent_evaluated_missions()` - 최근 평가 완료 미션 조회

### 5. UI 모듈 수정
- **`ui_pages/strategy/mission_detail.py`** (수정)
  - `_render_effect_comparison()` - 평가 결과 표시 확장
  - `_render_next_intervention()` - 다음 개입 제안 렌더링 추가
  - 완료 시 monitoring 상태로 자동 전환

- **`ui_pages/common/today_strategy_card.py`** (수정)
  - 상태 배지 표시 (실행중/감시중/판정완료)
  - 최근 평가 완료 미션 결과 요약 추가

- **`ui_pages/home/home_page.py`** (수정)
  - HOME 진입 시 monitoring 미션 자동 평가 훅 추가

- **`ui_pages/design_lab/design_center.py`** (수정)
  - ZONE A 하단에 "최근 전략 결과" 섹션 추가
  - ZONE D에 "코치 재개입" 섹션 추가 (worsened/no_change 시)

---

## 핵심 구현 내용

### 1. 감시 상태 개념

#### 상태 전환 흐름
- `active` → `completed` → `monitoring` → `evaluated`
- `active` → `abandoned` (포기)

#### 정책
- completed → 자동으로 monitoring 전환 (monitor_start_date 설정)
- monitoring → 숫자 충분해지면 evaluated 자동 판정 (evaluation_date 설정)

### 2. 자동 평가 엔진

#### 결과 타입 분류 (4개)
1. **improved**: 매출 ↑ AND (방문자 ↑ OR 객단가 ↑)
2. **worsened**: 매출 ↓ AND (방문자 ↓ OR 객단가 ↓)
3. **no_change**: 매출 변화 ±5% 이내
4. **data_insufficient**: 7일 데이터 미만

#### 코치 코멘트 자동 생성
- "매출이 개선되었습니다. 네이버방문자 증가가 기여했습니다."
- "매출이 더 감소했습니다. 상위 구조 문제 가능성이 커졌습니다."
- "변화가 미미합니다. 구조 변화가 아직 숫자에 반영되지 않았을 수 있습니다."

### 3. 다음 개입 결정 로직

#### 개입 타입 (4개)
1. **maintain** (improved): 현재 전략 유지 + 최적화
2. **pivot** (no_change): 다음 원인 후보로 전환
3. **escalate** (worsened): 상위 구조로 격상
4. **wait** (data_insufficient): 감시 유지

#### 원인 타입별 다음 후보 매핑
- 유입 감소형 → 객단가 하락형
- 객단가 하락형 → 판매량 하락형
- 판매량 하락형 → 주력메뉴 붕괴형
- 주력메뉴 붕괴형 → 원가율 악화형
- 원가율 악화형 → 구조 리스크형
- 구조 리스크형 → 유입 감소형

### 4. UI 노출 변경

#### HOME v2
- 진행중 미션 카드: 상태 배지 (🛠 실행중 / 👀 감시중 / 🧠 판정완료)
- 최근 평가 완료 미션: 결과 배지 + 코치 코멘트 + [근거 보기] 버튼

#### 가게 설계 센터
- ZONE A 하단: "최근 전략 결과" 섹션
- ZONE D: "코치 재개입" 섹션 (worsened/no_change 시 자동 상단 노출)

#### 미션 상세 화면
- 상태 타임라인: 생성 → 실행 → 감시 → 판정
- baseline vs after 비교 카드
- 코치 판정문
- 다음 추천 버튼: [다음 전략 시작] / [관련 설계실 이동]

---

## 데이터 정책 준수

### SSOT best_available 사용
- ✅ 평가 엔진에서 `load_best_available_daily_sales()` 사용
- ✅ sales 직접 조회 금지

### Graceful Fallback
- 평가 실패 시 안전하게 처리
- 데이터 부족 시 "data_insufficient" 반환

---

## 성능 최적화

### 캐시 활용
- `evaluate_mission_effect()`: `@st.cache_data(ttl=300)` (5분)
- mission_id/store_id 키 기반 캐싱

### 자동 평가 트리거
- HOME 진입 시 monitoring 미션 자동 평가 시도
- 조건 만족 시 즉시 evaluated로 전환

---

## 동작 흐름

1. HOME에서 전략 미션 생성 (10-7A)
2. 체크리스트 실행 (10-7B)
3. 완료 → monitoring 진입 (자동)
4. HOME 로드 시 `evaluate_mission_effect` 자동 시도
5. 조건 만족 → evaluated
6. 결과 저장 + 코치 판정 생성
7. HOME / 설계센터 / 미션페이지 반영
8. 다음 전략 자동 추천 (`decide_next_intervention`)

---

## 회귀 테스트 체크리스트

### ✅ 상태 전환
- [x] completed → monitoring 자동 전환되는지
- [x] monitoring → evaluated 자동 전환되는지
- [x] monitor_start_date, evaluation_date 정상 설정되는지

### ✅ 자동 평가
- [x] HOME 진입 시 monitoring 미션 자동 평가되는지
- [x] 결과 타입이 정확히 분류되는지
- [x] 코치 코멘트가 자동 생성되는지
- [x] strategy_mission_results에 정상 저장되는지

### ✅ 다음 개입
- [x] improved → maintain 전략 제안되는지
- [x] no_change → pivot 전략 제안되는지
- [x] worsened → escalate 전략 제안되는지
- [x] data_insufficient → wait 전략 제안되는지

### ✅ UI 노출
- [x] HOME에서 상태 배지 정상 표시되는지
- [x] 최근 평가 완료 미션 결과 요약 표시되는지
- [x] 설계센터에 "최근 전략 결과" 표시되는지
- [x] 설계센터에 "코치 재개입" 표시되는지 (worsened/no_change)
- [x] 미션 상세에 다음 개입 제안 표시되는지

---

## 주의사항

1. **SQL 실행**: `sql/phase10_strategy_execution.sql` 확장 부분을 Supabase SQL Editor에서 실행 필요
2. **자동 평가**: HOME 진입 시마다 평가 시도 (캐시로 성능 최적화)
3. **다음 전략**: 재개입 제안은 10-7A 전략 카드 엔진에 다시 투입 가능

---

## 완료일
2026-01-24
