# PHASE 10 / STEP 10-7B: 전략 카드 TOP3 생성 엔진 v1 완료

## 작업 개요
10-7A의 가게 상태 분류 결과 + 설계/매출 신호를 이용해서 "전략 카드 3장"을 안정적으로 생성.
신규 모듈 추가, 기존 페이지 로직 최소 침투, 데이터 부족 시에도 항상 3장 생성.

---

## 생성된 파일

### 신규 파일
- **`ui_pages/strategy/strategy_cards.py`** (신규)
  - `build_strategy_cards()` - 전략 카드 TOP3 생성 메인 함수
  - `_should_show_survival_card()` - 생존선 복구 카드 조건 체크
  - `_should_show_menu_profit_card()` - 마진 구조 복구 카드 조건 체크
  - `_should_show_ingredient_card()` - 원가 집중 분산 카드 조건 체크
  - `_should_show_portfolio_card()` - 포트폴리오 재배치 카드 조건 체크
  - `_should_show_sales_recovery_card()` - 매출 하락 원인 찾기 카드 조건 체크
  - `_build_survival_card()` - 생존선 복구 카드 빌드
  - `_build_menu_profit_card()` - 마진 구조 복구 카드 빌드
  - `_build_ingredient_card()` - 원가 집중 분산 카드 빌드
  - `_build_portfolio_card()` - 포트폴리오 재배치 카드 빌드
  - `_build_sales_recovery_card()` - 매출 하락 원인 찾기 카드 빌드
  - `_build_fallback_card()` - Fallback 카드 빌드
  - `_select_top3_cards()` - 우선순위 정렬 및 중복 제거
  - `_get_empty_cards()` - 빈 카드 반환 (fallback)

---

## 반환 스키마

```python
{
    "period": {"year": Y, "month": M},
    "store_state": {
        "code": "survival" | "recovery" | "restructure" | "growth",
        "label": "...",
        "scores": {...}
    },
    "cards": [
        {
            "rank": 1,
            "title": "...",  # 14자 내외, 명령형
            "goal": "...",   # 한 줄 목표
            "why": "...",    # 숫자 포함 근거
            "evidence": [...],  # 1~2개만
            "cta": {
                "label": "...",
                "page": "...",
                "params": {}  # tab 등
            }
        },
        {"rank": 2, ...},
        {"rank": 3, ...}
    ],
    "debug": {
        "rules_fired": [...],
        "notes": [...]
    }
}
```

---

## 카드 템플릿 (6개)

### 1. 생존선 복구 (Revenue)
- **조건**: revenue_score <= 35 OR break-even 대비 < 95%
- **CTA**: page="수익 구조 설계실", label="손익분기점부터 복구"
- **우선순위**: 1순위

### 2. 마진 구조 복구 (Menu Profit)
- **조건**: 마진 메뉴 0 OR 고원가율 메뉴 다수(>=3) OR menu_profit_score < 40
- **CTA**: page="메뉴 수익 구조 설계실", label="가격/마진 후보 보기"
- **우선순위**: 2순위

### 3. 원가 집중 분산 (Ingredient)
- **조건**: TOP3 집중도 >= 70% OR 고위험 재료 존재 OR ingredient_score < 40
- **CTA**: page="재료 등록", label="대체재/발주 구조 설계"
- **우선순위**: 3순위

### 4. 포트폴리오 재배치 (Portfolio)
- **조건**: 마진 메뉴 0 OR 역할 미분류 >= 30% OR 균형점수 < 40 OR menu_portfolio_score < 40
- **CTA**: page="메뉴 등록", label="역할/카테고리 정리"
- **우선순위**: 4순위

### 5. 매출 하락 원인 찾기 (Sales Recovery)
- **조건**: sales_score <= 45 OR 하락 신호 존재
- **CTA**: page="매출 하락 원인 찾기", label="원인 1분 진단"
- **우선순위**: 5순위

### 6. 데이터 채우기/설계 시작 (Fallback)
- **조건**: 데이터 부족 시 또는 3장 미만일 때
- **CTA**: page="가게 설계 센터", label="설계부터 채우기"
- **우선순위**: 최하위 (자동 채움)

---

## 카드 선택 로직

1. **조건 체크**: 각 카드 템플릿의 조건을 순서대로 체크
2. **우선순위 정렬**: survival → menu_profit → ingredient → portfolio → sales_recovery 순
3. **중복 제거**: 같은 CTA page는 첫 번째만 선택
4. **3장 보장**: 3장 미만이면 Fallback 카드로 채움

---

## 재사용된 함수

### 가게 상태 분류 (10-7A)
- `classify_store_state()` - 가게 상태 분류 결과

### 설계 데이터 (PHASE 10-4, 10-5)
- `get_design_state()` - 설계 상태 점수 (점수화 + 상태 판정)
- `get_design_insights()` - 설계 인사이트 (상세 데이터)

### 데이터 로더 (SSOT)
- `calculate_break_even_sales()` - 손익분기점
- `load_monthly_sales_total()` - 월 매출

---

## 문구 품질 규칙

### Title (14자 내외, 명령형)
- ✅ "생존선부터 복구하기"
- ✅ "마진 메뉴 만들기"
- ✅ "원가 집중도 분산"
- ✅ "메뉴 역할 분류하기"
- ✅ "매출 하락 원인 찾기"

### Goal (한 줄 목표)
- ✅ "예상 매출이 손익분기점을 넘도록 고정비/변동비 구조를 점검합니다."
- ✅ "마진 메뉴가 없어 수익 기여도가 낮습니다. 가격/원가 구조를 점검합니다."

### Why (숫자 포함 근거)
- ✅ "예상 매출(1,200,000원)이 손익분기점(1,500,000원)보다 300,000원 낮습니다."
- ✅ "마진 메뉴 0개 (전체 메뉴 있음)"
- ✅ "TOP3 재료 집중도 75%, 대체재 미설정 3개"

### Evidence (1~2개만, 짧게)
- ✅ ["손익분기점 대비 80%", "부족액 300,000원"]
- ✅ ["마진 메뉴 0개", "수익 기여도 낮음"]

---

## 성능/안전 가드

### 캐시 적용
- `@st.cache_data(ttl=300)` - 5분 캐시
- 키: `(store_id, year, month, state_payload hash)`

### 예외 처리
- 각 카드 빌드 시 try/except
- 실패 시 Fallback 카드로 대체
- `debug.notes`에 상세 기록

### 3장 보장
- 조건 만족 카드가 3장 미만이면 Fallback으로 채움
- 중복 CTA page는 첫 번째만 선택

---

## 사용 예시

```python
from ui_pages.strategy.strategy_cards import build_strategy_cards

# 전략 카드 생성
cards_result = build_strategy_cards(store_id, 2026, 1)

# 카드 확인
for card in cards_result["cards"]:
    print(f"Rank {card['rank']}: {card['title']}")
    print(f"  Goal: {card['goal']}")
    print(f"  Why: {card['why']}")
    print(f"  CTA: {card['cta']['label']} → {card['cta']['page']}")

# 디버그 정보
print(f"Rules fired: {cards_result['debug']['rules_fired']}")
```

---

## 완료일
2026-01-24
