# PHASE 10 / STEP 10-5: 설계 데이터 "활용" 자동 연결 완료

## 작업 개요
설계 DB화된 데이터(메뉴 포트폴리오/메뉴 수익/재료 구조/수익 구조)가 HOME v2 판결, 설계센터 판결, 설계센터 런치패드를 자동으로 개인화하도록 연결 완료.

---

## 생성/수정된 파일 목록

### 1. 통합 인사이트 집계 레이어 (신규)
- **`ui_pages/design_lab/design_insights.py`** (신규)
  - `get_design_insights(store_id, year, month)` - 통합 인사이트 집계
  - `_get_menu_portfolio_insights()` - 메뉴 포트폴리오 인사이트
  - `_get_menu_profit_insights()` - 메뉴 수익 구조 인사이트
  - `_get_ingredient_structure_insights()` - 재료 구조 인사이트
  - `_get_revenue_structure_insights()` - 수익 구조 인사이트

### 2. HOME v2 판결 업그레이드
- **`ui_pages/home/home_verdict.py`** (수정)
  - `get_coach_verdict()` - 설계 인사이트를 우선 근거로 사용
  - `_check_design_based_risks()` - 설계 DB 기반 위험 판단 추가

### 3. 설계센터 런치패드 Top3 개인화
- **`ui_pages/design_lab/design_center.py`** (수정)
  - `_get_top3_launchpad_actions()` - 설계 인사이트 기반 Top3 액션 선정
  - 런치패드 UI: 우선 노출 3개 + 나머지 expander

### 4. 네비게이션/딥링크
- **`ui_pages/menu_management.py`** (수정)
  - session_state 기반 초기 탭 제어 (전략 실행 탭 기본 열기)
- **`ui_pages/menu_profit_design_lab.py`** (수정)
  - session_state 기반 초기 탭 제어
- **`ui_pages/ingredient_management.py`** (수정)
  - session_state 기반 초기 탭 제어
- **`ui_pages/revenue_structure_design_lab.py`** (수정)
  - session_state 기반 초기 탭 제어

---

## 핵심 구현 내용

### 1. 통합 인사이트 집계 레이어

#### 반환 구조
```python
{
  "menu_portfolio": {
    "has_data": bool,
    "margin_menu_count": int,
    "role_unclassified_ratio": float,
    "bait_ratio": float,
    "volume_ratio": float,
    "portfolio_balance_score": int,
    "primary_issue": "MARGIN_ZERO" | "UNCLASSIFIED_HIGH" | "BAIT_EXCESS" | "BALANCE_POOR" | None
  },
  "menu_profit": {
    "has_data": bool,
    "high_cogs_ratio_menu_count": int,
    "worst_cogs_ratio": float,
    "low_contribution_menu_count": int,
    "primary_issue": "COGS_VERY_HIGH" | "COGS_HIGH_COUNT" | "CONTRIBUTION_LOW" | None
  },
  "ingredient_structure": {
    "has_data": bool,
    "top3_concentration": float,  # 0~1
    "high_risk_ingredient_count": int,
    "missing_substitute_count": int,
    "missing_order_type_count": int,
    "primary_issue": "CONCENTRATION_HIGH_NO_SUBSTITUTE" | "CONCENTRATION_HIGH" | "HIGH_RISK_NO_SUBSTITUTE" | "ORDER_TYPE_MISSING" | None
  },
  "revenue_structure": {
    "has_data": bool,
    "break_even_sales": float,
    "expected_month_sales": float,
    "break_even_gap_ratio": float,
    "primary_issue": "BREAK_EVEN_GAP_LARGE" | "BREAK_EVEN_BELOW" | None
  }
}
```

#### 구현 원칙
- 설계 DB 데이터가 없으면 `has_data=False`로 깔끔히 처리
- 계산은 가벼운 룰 기반 (성능/안정성 우선)
- 기존 helper/coach_data 재사용

### 2. HOME v2 판결 업그레이드

#### 판결 룰 (우선순위)
1. **설계 DB 기반 판단** (우선순위 높음)
   - 마진 메뉴 0개 (margin_menu_count == 0 AND 메뉴 >= 3)
     → "메뉴 수익 구조 위험" + CTA: 메뉴 수익 구조 설계실
   - TOP3 재료 집중 >= 0.70 AND missing_substitute_count > 0
     → "재료 구조 위험" + CTA: 재료 구조 설계실
   - break_even_gap_ratio < 1.0
     → "수익 구조 위험" + CTA: 수익 구조 설계실

2. **운영 데이터 기반 판단** (fallback)
   - 기존 `_check_revenue_structure_risk()`, `_check_menu_profit_risk()`, `_check_ingredient_structure_risk()` 유지

### 3. 설계센터 런치패드 Top3 개인화

#### Top3 선정 룰 (점수 기반)
- `break_even_gap_ratio < 0.9` => +100점
- `top3_concentration >= 0.7 AND missing_substitute_count > 0` => +90점
- `margin_menu_count == 0` => +85점
- `role_unclassified_ratio >= 0.3` => +60점
- `high_cogs_ratio_menu_count >= 3` => +70점

#### UI 구조
- **우선 노출 3개**: 점수 상위 3개 액션
- **나머지 액션**: expander("더보기") 안에 배치
- 중복 제거: 같은 page는 최고 점수만 유지

### 4. 네비게이션/딥링크

#### 구현 방식
- session_state 플래그: `_initial_tab_{page_key}` = "execute"
- 페이지 진입 시 플래그 확인하여 탭 순서 변경
- "전략 실행" 탭을 첫 번째로 배치 (플래그 있을 때만)
- 플래그는 한 번만 적용 후 제거

#### 적용 페이지
- 메뉴 포트폴리오 설계실 (`메뉴 등록`)
- 메뉴 수익 구조 설계실 (`메뉴 수익 구조 설계실`)
- 재료 구조 설계실 (`재료 등록`)
- 수익 구조 설계실 (`수익 구조 설계실`)

---

## 품질/안전 가드

### 1. 데이터 부족 처리
- 모든 함수에서 `has_data=False` 반환 시 안전하게 처리
- None 체크 및 기본값 설정

### 2. 캐시 활용
- `get_design_insights()`: `@st.cache_data(ttl=300)` 적용
- store_id/year/month 키 기반 캐싱

### 3. 에러 처리
- 모든 함수에 try-except 적용
- 에러 발생 시 빈 인사이트 반환 (앱 깨짐 방지)

---

## 회귀 테스트 체크리스트

### ✅ 기본 기능
- [x] 설계 데이터 없는 신규 매장에서도 홈/센터 정상 작동
- [x] 설계 데이터 있을 때 판결/CTA가 바뀌는지 확인
- [x] Top3 버튼이 상태에 따라 달라지는지 확인

### ✅ HOME v2 판결
- [x] 설계 DB 기반 판결이 우선 적용되는지
- [x] 마진 메뉴 0개 시 "메뉴 수익 구조 위험" 판결
- [x] 재료 집중도 높을 때 "재료 구조 위험" 판결
- [x] 손익분기점 미달 시 "수익 구조 위험" 판결
- [x] 데이터 부족 시 안전하게 처리

### ✅ 설계센터 런치패드
- [x] Top3 액션이 설계 인사이트 기반으로 선정되는지
- [x] 우선 노출 3개가 점수 상위인지
- [x] 나머지 액션이 expander에 있는지
- [x] 중복 제거가 정상 작동하는지

### ✅ 네비게이션/딥링크
- [x] 런치패드에서 버튼 클릭 시 해당 설계실로 이동
- [x] "전략 실행" 탭이 기본으로 열리는지 (플래그 있을 때)
- [x] 플래그가 한 번만 적용되는지
- [x] 4개 설계실 모두 정상 작동하는지

---

## HOME 판결 룰/우선순위 정리

### 우선순위 1: 설계 DB 기반 판단
1. **메뉴 수익 구조 위험**
   - 조건: `margin_menu_count == 0 AND 메뉴 >= 3`
   - 판결: "메뉴 수익 구조가 위험합니다. 마진 메뉴가 없어 수익 기여도가 낮습니다."
   - CTA: 메뉴 수익 구조 설계실

2. **재료 구조 위험**
   - 조건: `top3_concentration >= 0.70 AND missing_substitute_count > 0`
   - 판결: "재료 구조가 위험합니다. 상위 3개 재료에 과도하게 집중되어 있고 대체재가 설정되지 않았습니다."
   - CTA: 재료 구조 설계실

3. **수익 구조 위험**
   - 조건: `break_even_gap_ratio < 1.0`
   - 판결: "수익 구조가 위험합니다. 예상 매출이 손익분기점보다 낮습니다."
   - CTA: 수익 구조 설계실

### 우선순위 2: 운영 데이터 기반 판단 (fallback)
- 기존 로직 유지 (`_check_revenue_structure_risk`, `_check_menu_profit_risk`, `_check_ingredient_structure_risk`)

---

## 런치패드 Top3 선정 룰 정리

### 점수 체계
- `break_even_gap_ratio < 0.9`: +100점
- `top3_concentration >= 0.7 AND missing_substitute_count > 0`: +90점
- `margin_menu_count == 0`: +85점
- `high_cogs_ratio_menu_count >= 3`: +70점
- `role_unclassified_ratio >= 0.3`: +60점
- 기본 액션: +50점

### 액션 후보
1. 📈 손익분기점 갱신 → 수익 구조 설계실
2. 🥬 원가 집중/대체재 설계 → 재료 구조 설계실
3. 💰 고원가율 메뉴 정리 → 메뉴 수익 구조 설계실
4. 📊 포트폴리오 미분류 정리 → 메뉴 등록
5. 📉 매출 하락 원인 찾기 → 매출 관리
6. 🏠 홈으로 돌아가기 → 홈

---

## 주의사항

1. **캐시 무효화**: 설계 데이터 변경 시 `get_design_insights.clear()` 호출 필요
2. **성능**: 인사이트 집계는 캐시를 활용하지만, 첫 로드 시 약간의 지연 가능
3. **데이터 부족**: 설계 DB에 데이터가 없어도 앱이 정상 작동 (has_data=False 처리)

---

## 완료일
2026-01-23
