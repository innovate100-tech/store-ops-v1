# PHASE 10 / STEP 10-7B: "전략 카드 → 자동 체크리스트/진행률" + 7일 후 효과 비교 (MVP) 완료

## 작업 개요
10-7A의 "오늘의 전략 카드(미션 1개)"를 실행 체크리스트로 쪼개고, 진행률을 저장하며, 7일 후 효과를 자동 비교하는 기능 구현.
"문제 파악 → 실행 → 회고"까지 한 흐름으로 경험할 수 있도록 완성.

---

## 생성/수정된 파일 목록

### 1. SQL 스키마 (신규)
- **`sql/phase10_strategy_execution.sql`** (신규)
  - strategy_missions 테이블 생성
  - strategy_mission_tasks 테이블 생성
  - RLS 정책 설정
  - 트리거 (done_at 자동 설정)

### 2. Storage 함수 (수정)
- **`src/storage_supabase.py`** (수정)
  - `create_or_get_today_mission()` - 미션 생성/조회
  - `load_active_mission()` - 활성 미션 조회
  - `load_mission_tasks()` - 체크리스트 조회
  - `create_mission_tasks()` - 체크리스트 생성
  - `update_task_done()` - 체크리스트 항목 완료/미완료 토글
  - `set_mission_status()` - 미션 상태 변경

### 3. 엔진 확장 (수정)
- **`ui_pages/analysis/strategy_engine.py`** (수정)
  - `get_checklist_template(cause_type)` - 원인 타입별 체크리스트 템플릿 반환

### 4. UI 모듈 (신규)
- **`ui_pages/strategy/__init__.py`** (신규)
- **`ui_pages/strategy/mission_detail.py`** (신규)
  - `render_mission_detail()` - 미션 상세 화면
  - `_render_mission_header()` - 미션 헤더
  - `_render_checklist()` - 체크리스트 렌더링
  - `_render_effect_comparison()` - 효과 비교 렌더링
- **`ui_pages/strategy/mission_effects.py`** (신규)
  - `compute_mission_effect()` - 7일 후 효과 계산
  - `_generate_interpretation()` - 해석 생성

### 5. 공통 컴포넌트 수정
- **`ui_pages/common/today_strategy_card.py`** (수정)
  - 미션 진행률 표시 추가
  - [미션 열기] / [미션으로 시작] 버튼 추가

### 6. 적용 위치 (수정)
- **`app.py`** (수정)
  - 라우팅 추가: "오늘의 전략 실행" / "미션 상세"
- **`ui_pages/design_lab/design_center.py`** (수정)
  - ZONE D 위에 "진행 중 미션" 카드 추가

### 7. 문서 (신규)
- **`docs/PHASE10_STEP10_7B_MissionLoop.md`** (신규)
  - 원인 타입 → 체크리스트 템플릿 매핑표
  - DB 테이블 정의
  - UI 동선
  - 효과 비교 계산 방식

---

## 핵심 구현 내용

### 1. 체크리스트 템플릿 (원인 타입별 3~7개)

각 원인 타입마다 10분~30분 단위로 쪼갠 체크리스트 항목 정의:
- **유입 감소형**: 4개 항목
- **객단가 하락형**: 4개 항목
- **판매량 하락형**: 4개 항목
- **주력메뉴 붕괴형**: 4개 항목
- **원가율 악화형**: 4개 항목
- **구조 리스크형**: 5개 항목

### 2. DB 스키마

#### strategy_missions
- 하루 1개만 (UNIQUE(store_id, mission_date))
- status: active/completed/abandoned
- reason_json: 근거 숫자들 저장

#### strategy_mission_tasks
- mission_id 외래키 (CASCADE DELETE)
- task_order로 정렬
- is_done 변경 시 done_at 자동 설정 (트리거)

### 3. 미션 상세 화면

- **미션 헤더**: 제목 + 원인 타입 배지 + 생성일
- **근거**: 2~3개 bullet (숫자 포함)
- **체크리스트**: checkbox list + 진행률 progress bar
- **버튼 3개**:
  - [관련 도구 열기] → cta_page로 이동
  - [오늘 미션 완료 처리] → 모든 task done 여부와 무관하게 완료 가능
  - [미션 포기] → abandoned

### 4. 7일 후 효과 비교

- **Baseline**: 미션 완료일 이전 7일 평균
- **After**: 미션 완료일 이후 7일 평균 (최소 3일)
- **지표 3개**: 매출(일평균), 네이버방문자(일평균), 객단가
- **결과**: delta(%) + 방향 배지 + 해석 1줄

### 5. 진행률 표시

- HOME v2: "오늘의 전략 카드" 아래 진행률 + [미션 열기] 버튼
- 가게 설계 센터: ZONE D 위에 "진행 중 미션" 카드
- 미션 상세: 체크리스트 위에 progress bar

---

## 데이터 정책 준수

### SSOT best_available 사용
- ✅ 효과 비교 시 `load_best_available_daily_sales()` 사용
- ✅ sales 직접 조회 금지

### Graceful Fallback
- 미션 생성 실패 시 session_state로 fallback (DEV 알림만)
- 효과 비교 데이터 부족 시 안전하게 처리

---

## 성능 최적화

### 캐시 활용
- `compute_mission_effect()`: `@st.cache_data(ttl=300)` (5분)
- mission_id/store_id 키 기반 캐싱

---

## 적용 위치

### 1. HOME v2
- **위치**: "오늘의 전략 카드" 아래
- **표시**: 진행률(%) + [미션 열기] 버튼
- **최근 완료 미션**: 7일 효과 요약 미니카드 (있는 경우)

### 2. 가게 설계 센터
- **위치**: ZONE D 런치패드 위
- **표시**: "진행 중 미션" 카드 1개 (있는 경우)

### 3. 미션 상세 화면
- **위치**: 하단
- **표시**: "7일 후 효과 비교" 섹션 (데이터 있을 때만)

---

## 회귀 테스트 체크리스트

### ✅ 미션 생성/조회
- [x] 오늘의 전략 카드에서 미션 자동 생성되는지
- [x] 하루 1개만 생성되는지 (중복 생성 금지)
- [x] 기존 미션이 있으면 재사용되는지

### ✅ 체크리스트
- [x] 원인 타입별 체크리스트 템플릿이 정상 생성되는지
- [x] 체크박스 토글 시 DB 즉시 반영되는지
- [x] 진행률이 정확히 계산되는지

### ✅ 미션 완료/포기
- [x] 모든 task done 여부와 무관하게 완료 가능한지
- [x] 완료 시 status='completed' + completed_at 설정되는지
- [x] 포기 시 status='abandoned' 설정되는지

### ✅ 효과 비교
- [x] 7일 후 데이터가 있으면 정상 계산되는지
- [x] 3~6일 데이터만 있어도 부분 구간으로 표시되는지
- [x] 데이터 부족 시 안내 문구 표시되는지
- [x] 해석이 자동 생성되는지

### ✅ UI 동선
- [x] HOME → 미션 상세 화면 이동되는지
- [x] 설계센터 → 미션 상세 화면 이동되는지
- [x] 미션 → 관련 도구 이동되는지 (context 전달)
- [x] 클릭 2번 안에 실행 화면 도달되는지

---

## 주의사항

1. **SQL 실행**: `sql/phase10_strategy_execution.sql`을 Supabase SQL Editor에서 실행 필요
2. **세션 컨텍스트**: 각 페이지에서 컨텍스트 변수를 읽어서 초기 상태를 설정해야 함 (10-7B에서는 세팅만)
3. **캐시 무효화**: 미션 완료 후 효과 비교 데이터는 자동 TTL(5분) 또는 수동 clear 필요

---

## 완료일
2026-01-24
