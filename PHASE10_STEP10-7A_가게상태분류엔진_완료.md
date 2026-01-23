# PHASE 10 / STEP 10-7A: 가게 상태 분류(Store State) 엔진 v1 완료

## 작업 개요
"전략 자동 생성"의 1단계로, 가게 상태를 4가지로 분류하는 로직 구현.
기존 기능/페이지 변경 없이 신규 모듈로만 추가. 데이터 부족 시에도 크래시 없이 안전하게 처리.

---

## 생성된 파일

### 신규 파일
- **`ui_pages/strategy/store_state.py`** (신규)
  - `classify_store_state()` - 가게 상태 분류 메인 함수
  - `_calculate_revenue_score()` - Revenue Score 계산
  - `_calculate_sales_score()` - Sales Score 계산
  - `_calculate_menu_score()` - Menu Score 계산
  - `_calculate_ingredient_score()` - Ingredient Score 계산
  - `_classify_state()` - 상태 분류 로직
  - `_get_empty_state()` - 빈 상태 반환 (fallback)

---

## 반환 스키마

```python
{
    "period": {"year": Y, "month": M},
    "state": {
        "code": "survival" | "recovery" | "restructure" | "growth",
        "label": "생존선 복구" | "회복 모드" | "구조 개편" | "성장 최적화"
    },
    "scores": {
        "sales": 0-100,
        "menu": 0-100,
        "ingredient": 0-100,
        "revenue": 0-100,
        "overall": 0-100
    },
    "signals": [
        {
            "key": "...",
            "status": "ok" | "warn" | "risk",
            "value": "...",
            "note": "..."
        }
    ],
    "primary_reason": "한 줄 설명",
    "evidence": [
        {
            "title": "...",
            "value": "...",
            "delta": "..." | None,
            "note": "..."
        }
    ],
    "debug": {
        "inputs_used": [...],
        "notes": [...]
    }
}
```

---

## 점수 계산 로직

### 1. Revenue Score (0-100)
- **기준**: 손익분기점 대비 예상매출 비율 (r = expected_sales / break_even_sales)
- **룰**:
  - r < 0.95 → 20~35점 (risk)
  - 0.95 <= r < 1.05 → 40~60점 (warn)
  - r >= 1.05 → 70~90점 (ok)
- **데이터 소스**: `calculate_break_even_sales()`, `load_monthly_sales_total()`

### 2. Sales Score (0-100)
- **기준**: 최근 14일 vs 전주 14일 매출 변화율
- **룰**:
  - 변화율 < -15% → 20~40점 (하락 강함)
  - -15% <= 변화율 < -5% → 40~60점 (하락 보통)
  - -5% <= 변화율 < 5% → 60~80점 (안정)
  - 변화율 >= 5% → 80~90점 (상승)
- **데이터 소스**: `load_best_available_daily_sales()` (SSOT)

### 3. Menu Score (0-100)
- **기준**: 설계 상태 점수 (포트폴리오 + 수익 구조 평균)
- **룰**: `get_design_state()`의 `menu_portfolio.score`와 `menu_profit.score` 평균
- **데이터 소스**: `get_design_state()` (PHASE 10-5에서 구현)

### 4. Ingredient Score (0-100)
- **기준**: 설계 상태 점수
- **룰**: `get_design_state()`의 `ingredient_structure.score` 그대로 사용
- **데이터 소스**: `get_design_state()`

### 5. Overall Score (0-100)
- **가중 평균**: revenue 40% + sales 30% + menu 15% + ingredient 15%

---

## 상태 분류 규칙

### 1. Survival (생존선 복구)
- 조건:
  - (expected_sales < break_even_sales) OR (revenue_score <= 35)
- 우선순위: 최우선

### 2. Recovery (회복 모드)
- 조건:
  - Survival이 아니고, sales_score <= 45
- 우선순위: 2순위

### 3. Restructure (구조 개편)
- 조건:
  - Survival/Recovery 아니고, (menu_score < 40 OR ingredient_score < 40) AND sales_score >= 50
- 우선순위: 3순위

### 4. Growth (성장 최적화)
- 조건: 그 외 (전반 안정/상승)
- 우선순위: 4순위

---

## 재사용된 함수

### 데이터 로더 (SSOT 준수)
- `load_best_available_daily_sales()` - 매출/네이버방문자 (SSOT)
- `load_monthly_sales_total()` - 월 매출 합계
- `calculate_break_even_sales()` - 손익분기점 계산
- `load_official_daily_sales()` - 마감률/스트릭 계산용 (필요 시)

### 설계 상태 로더 (PHASE 10-5)
- `get_design_state()` - 설계 상태 통합 로드 (점수화 + 상태 판정)

---

## 성능/안전 가드

### 캐시 적용
- `@st.cache_data(ttl=300)` - 5분 캐시
- 키: `(store_id, year, month)`

### 예외 처리
- 각 데이터 조각 로드 시 try/except
- 실패 시 `debug.notes`에 기록
- 중립 값(50점)으로 진행하여 크래시 방지

### 데이터 부족 처리
- 해당 축 score를 50(중립)로 설정
- `signals`에 "데이터 부족" 기록
- `debug.notes`에 상세 기록

---

## 사용 예시

```python
from ui_pages.strategy.store_state import classify_store_state

# 가게 상태 분류
state = classify_store_state(store_id, 2026, 1)

# 상태 코드 확인
print(state["state"]["code"])  # "survival" | "recovery" | "restructure" | "growth"
print(state["state"]["label"])  # "생존선 복구" | "회복 모드" | "구조 개편" | "성장 최적화"

# 점수 확인
print(state["scores"]["overall"])  # 0-100

# 신호 확인
for signal in state["signals"]:
    print(f"{signal['key']}: {signal['status']} - {signal['value']}")

# 근거 확인
for ev in state["evidence"]:
    print(f"{ev['title']}: {ev['value']}")
```

---

## 완료일
2026-01-24
