# PHASE 10 / STEP 10-7C: 전략 실행 로드맵 TOP3 + 전략 보드(페이지) v1 완료

## 작업 개요
10-7A/B 결과를 사용자에게 보여주고, "이번 주 할 일 TOP3"을 버튼으로 바로 실행시키는 페이지 구현.
1페이지로 끝내고, HOME/설계센터에서 들어오는 진입 버튼만 최소 수정.

---

## 생성된 파일

### 신규 파일
- **`ui_pages/strategy/__init__.py`** (신규)
  - 전략 실행 모듈 초기화

- **`ui_pages/strategy/roadmap.py`** (신규)
  - `build_weekly_roadmap()` - 이번 주 실행 로드맵 TOP3 생성
  - `_extract_task_from_card()` - 카드에서 실행형 작업 문구 추출
  - `_estimate_task_time()` - 작업 시간 추정 (10m/30m/60m)
  - `_get_default_roadmap()` - 기본 로드맵 (데이터 부족 시)

- **`ui_pages/strategy/strategy_board.py`** (신규)
  - `render_strategy_board()` - 전략 보드 페이지 메인 렌더링
  - `_render_state_badge()` - 상단 배지 (상태 + 점수)
  - `_render_evidence_section()` - 섹션 1: 근거 3개 카드
  - `_render_strategy_cards_section()` - 섹션 2: 전략 카드 TOP3
  - `_render_roadmap_section()` - 섹션 3: 이번 주 실행 TOP3

---

## 수정된 파일

### app.py
- **사이드바 메뉴 추가**: "🏠 HOME" 카테고리에 "전략 보드" 추가
- **라우팅 추가**: `elif page == "전략 보드":` 라우팅 연결

### ui_pages/home/home_page.py
- **버튼 추가**: ZONE 1 상단에 "📌 이번 달 전략 보기" 버튼 추가
- 클릭 시 `st.session_state["current_page"] = "전략 보드"`로 이동

### ui_pages/design_lab/design_center.py
- **버튼 추가**: 상단에 "📌 이번 달 전략 보드" 버튼 추가
- "이번 주 구조 점검 완료 처리" 버튼과 나란히 배치 (2열)

---

## 전략 보드 페이지 구조

### 제목
- "전략 보드 (이번 달)" 📌

### 상단 배지
- 상태 라벨 (예: "생존선 복구" 🔴)
- 종합 점수 (0-100점)

### 섹션 1: 근거 (Evidence)
- 최대 3개 카드 표시
- 각 카드: 제목, 값, 변화량, 메모
- 데이터 없으면 안내 문구

### 섹션 2: 전략 카드 TOP3
- 각 카드:
  - Rank + Title
  - 목표 (Goal)
  - 이유 (Why)
  - 근거 (Evidence) 1~2개
  - CTA 버튼 (페이지 이동)

### 섹션 3: 이번 주 실행 TOP3
- 각 항목:
  - Rank + Task
  - 시간 추정 (⏱️ 10m/30m/60m)
  - CTA 버튼 (페이지 이동)

### DEV 전용 (expander)
- Debug 정보 표시 (state, cards, roadmap JSON)

---

## 로드맵 생성 규칙

### 작업 시간 추정 (estimate)
- **60m**: revenue/ingredient 구조 작업
  - "수익 구조 설계실"
  - "재료 등록"
- **30m**: portfolio 정리, 메뉴 수익 구조
  - "메뉴 등록"
  - "메뉴 수익 구조 설계실"
  - "설계 센터"
- **10m**: 매출 원인 찾기
  - "매출 하락 원인 찾기"

### 작업 문구 (task)
- 카드의 `title`을 그대로 사용 (명령형)
- 없으면 `goal`에서 추출
- "오늘:", "이번 주:" 같은 과장 금지

---

## 진입 경로

### 1. 사이드바
- "🏠 HOME" → "전략 보드" 클릭

### 2. HOME v2
- ZONE 1 상단: "📌 이번 달 전략 보기" 버튼

### 3. 가게 설계 센터
- 상단: "📌 이번 달 전략 보드" 버튼

---

## 안정성 가드

### 예외 처리
- `classify_store_state()`, `build_strategy_cards()` 실패 시
- Fallback: 안내 문구 + "가게 설계 센터로 이동" 버튼

### 캐시 활용
- `@st.cache_data(ttl=300)` - 10-7A/B에서 이미 적용
- 키: `(store_id, year, month)`

### 데이터 부족 처리
- Evidence 없으면 안내 문구
- 카드 없으면 기본 카드 표시
- 로드맵 없으면 기본 로드맵 표시

---

## 완료 체크리스트

- [x] 사이드바 전략 보드 진입 OK
- [x] HOME 버튼으로 진입 OK
- [x] 설계센터 버튼으로 진입 OK
- [x] 전략 카드 3장 항상 표시
- [x] 실행 TOP3 항상 표시
- [x] CTA 이동 정상
- [x] DEV 모드 debug 정보 표시

---

## 사용 예시

```python
# 전략 보드 페이지 진입
st.session_state["current_page"] = "전략 보드"
st.rerun()

# 로드맵 생성 (내부)
from ui_pages.strategy.roadmap import build_weekly_roadmap
roadmap = build_weekly_roadmap(cards_result)
# [
#   {"rank": 1, "task": "생존선부터 복구하기", "estimate": "60m", "cta": {...}},
#   {"rank": 2, "task": "마진 메뉴 만들기", "estimate": "30m", "cta": {...}},
#   {"rank": 3, "task": "매출 하락 원인 찾기", "estimate": "10m", "cta": {...}}
# ]
```

---

## 완료일
2026-01-24
