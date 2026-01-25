# 데이터 입력 센터 페이지 구조 정리 (v4.1)

## 📋 개요
- **파일**: `ui_pages/input/input_hub.py`
- **메인 함수**: `render_input_hub_v3()`
- **목적**: 매장을 시스템으로 보여주는 '데이터 자산 허브'
- **버전**: v4.1 (시스템 허브화)

---

## 🎨 CSS 주입 계층

### 1. `inject_input_hub_animations_css()`
- **계층**: FX (1회 주입)
- **내용**: 
  - 애니메이션 keyframes: `fadeInUp`, `shimmer-bg`, `wave-move`, `pulse-ring`
  - 기본 상태 보장: `opacity: 1 !important` (실패해도 보이게)
  - `prefers-reduced-motion` 지원
- **가드**: `_ps_input_hub_anim_css_injected`

### 2. `inject_input_hub_ultra_premium_css()`
- **계층**: FX (1회 주입)
- **내용**:
  - 배경 레이어 (::before, ::after)
  - 상단 Neon Bar (position: fixed, z-index: 0)
  - 배경 메시/그리드 (position: fixed, inset: 0, z-index: 0)
  - 컨텐츠 wrapper (z-index: 10)
  - `prefers-reduced-motion` 지원
- **가드**: `_ps_ultra_css_injected`
- **토글**: `_ps_disable_ultra_css` (False면 비활성화)

---

## 🧠 시스템 진단 함수 (v4.1 신규)

### 1. `detect_system_stage(assets, has_daily_close)`
- **목적**: 현재 시스템 단계 감지 (LEVEL 1-4)
- **단계 정의**:
  - LEVEL 1 기록 단계: 마감만 있음 또는 메뉴/재료 미완성
  - LEVEL 2 구조 단계: 메뉴/재료 있음, 레시피 미완성
  - LEVEL 3 수익 단계: 레시피 80% 이상, 목표 미설정
  - LEVEL 4 전략 단계: 목표 + 정산 활성
- **반환**: `{"level": 1-4, "name": "...", "description": "..."}`

### 2. `detect_system_bottleneck(assets, has_daily_close, system_stage)`
- **목적**: 현재 단계 기준 단일 병목 감지
- **반환**: `{"bottleneck": "...", "message": "...", "details": [...], "impact": "..."}`

### 3. `get_system_recommendation(bottleneck, assets)`
- **목적**: 시스템 추천 액션 생성
- **반환**: 
  ```python
  {
    "primary": {"label": "...", "page_key": "...", "description": "...", "button_text": "..."},
    "secondary": {...} | None,
    "relief": ["지금은 안 해도 되는 입력", ...]
  }
  ```

---

## 📊 데이터 조회 함수

### 1. `_count_completed_checklists_last_n_days(store_id, days=14)`
- **목적**: 최근 N일간 완료된 QSC 체크리스트 개수 조회
- **데이터 소스**: `health_check_sessions` 테이블
- **반환**: 완료된 체크리스트 개수 (int)

### 2. `_is_current_month_settlement_done(store_id)`
- **목적**: 이번 달 정산 완료 여부 확인
- **데이터 소스**: `load_actual_settlement_items()`
- **반환**: 완료 여부 (bool)

### 3. `_get_today_recommendations(store_id)`
- **목적**: 오늘 입력해야 할 항목 추천 리스트 생성
- **데이터 소스**: 
  - `get_day_record_status()` - 오늘 마감 상태
  - `health_check_sessions` - QSC 점검 이력
  - `load_actual_settlement_items()` - 월간 정산 상태
- **반환**: 추천 항목 리스트
  ```python
  [
    {
      "status": "pending" | "completed",
      "message": "📝 오늘 마감 필요",
      "button_label": "📝 일일 마감",
      "page_key": "일일 입력(통합)",
      "priority": 1,
      "summary": "100,000원 / 50명"
    },
    ...
  ]
  ```
- **우선순위**:
  - Priority 1: 오늘 마감
  - Priority 4: QSC 점검
  - Priority 5: 월간 정산

### 4. `_get_asset_readiness(store_id)`
- **목적**: 입력 데이터 자산 완성도 조회
- **데이터 소스**:
  - `menu_master.csv` - 메뉴 개수, 가격 누락 개수
  - `ingredient_master.csv` - 재료 개수, 단가 누락 개수
  - `recipes.csv` - 레시피 완성도
  - `targets.csv` - 목표 설정 여부
- **반환**: 자산 완성도 딕셔너리
  ```python
  {
    "menu_count": 100,
    "missing_price": 5,
    "ing_count": 50,
    "missing_cost": 2,
    "recipe_rate": 85.0,
    "has_target": True
  }
  ```

---

## 🎴 UI 컴포넌트 함수

### 1. `_hub_status_card(title, value, sub, status, delay_class)`
- **목적**: 상태 카드 렌더링 (오늘의 마감, QSC, 정산 등)
- **파라미터**:
  - `title`: 카드 제목
  - `value`: 메인 값 (예: "✅ 완료")
  - `sub`: 부가 정보 (예: "100,000원 / 50명")
  - `status`: "pending" | "completed" | "warning"
  - `delay_class`: 애니메이션 지연 클래스 ("delay-1", "delay-2", ...)
- **스타일**:
  - `backdrop-filter`는 `_ps_fx_blur_on` 토글로 제어
  - 상태별 색상: completed(녹색), warning(주황), pending(회색)

### 2. `_hub_asset_card(title, value, icon, delay_class)`
- **목적**: 자산 카드 렌더링 (메뉴, 재료, 레시피, 목표)
- **파라미터**:
  - `title`: 카드 제목
  - `value`: 값 (예: "100개", "85%")
  - `icon`: 아이콘 이모지
  - `delay_class`: 애니메이션 지연 클래스

---

## 🏗️ 메인 렌더링 구조

### `render_input_hub_v3()`

#### 1. 초기화 및 CSS 주입
- 페이지 헤더 렌더링
- Ultra Premium CSS 주입
- 애니메이션 CSS 주입
- 컨텐츠 wrapper 시작 (`<div data-ps-scope="input_hub" class="ps-hub-bg">`)

#### 2. 데이터 로드
- `_get_today_recommendations()` - 오늘 추천 항목
- `_get_asset_readiness()` - 자산 완성도
- 디지털 성숙도 점수 계산 (0-100점)
  - 메뉴 가격 완성: 25점
  - 재료 단가 완성: 25점
  - 레시피 완성도 80% 이상: 25점
  - 목표 설정: 25점

#### 3. ZONE 구조 (v4.1)

##### 🟦 ZONE 0: 데이터 자산 가이드 (시스템 정체성 선언)
- **제목**: "💡 데이터 자산 가이드"
- **본문**: "이 앱은 '감'이 아니라 데이터 자산으로 매장을 운영하게 만듭니다. 아래 항목들이 채워질수록, 매장 운영이 시스템이 됩니다."
- **표시 항목**:
  - MATURITY LEVEL (0-100%) - 유지
  - 진행 바 (애니메이션) - 유지
- **하단 문구**: "🚩 비어 있는 데이터를 채우면 정밀 리포트/전략 기능이 단계적으로 열립니다. 입력은 일이 아니라, 매장의 운영 시스템을 만드는 과정입니다."
- **애니메이션**: `guide-card-animated`, `shimmer-overlay`

##### 🟥 ZONE 1: 시스템 진단 & 추천 블록 (v4.1 신규 핵심)
- **제목**: "🧠 시스템 진단 요약"
- **성격**: 할 일 목록 ❌ → 시스템 판독기 ✅
- **구성 요소**:
  1. **CURRENT SYSTEM STAGE**: 현재 단계 (LEVEL 1-4) 및 설명
  2. **SYSTEM BOTTLENECK**: 현재 병목 (단 하나만 표시)
  3. **SYSTEM NEXT ACTION**: 
     - PRIMARY ACTION: 병목 해결 액션 (버튼 1개)
     - SECONDARY ACTION: 기준 데이터/전략 관련 (선택)
  4. **RELIEF BLOCK**: "지금은 안 해도 되는 입력" (선택)
  5. **철학 문장**: "이 앱은 일을 시키기 위해 존재하지 않습니다. 매장을 시스템으로 보게 만들기 위해 존재합니다."

##### 🟩 ZONE 2: 우리 매장 데이터 지도
- **제목**: "🗺️ 우리 매장 데이터 지도"
- **성격**: "오늘 할 일" ❌ → "데이터 종류" 기준 ✅
- **카드 4개** (4열 레이아웃):
  1. 일별 운영 데이터
     - 현재 보유 여부
     - 최근 입력일
     - 목적: "이 데이터는 매출 추이 분석의 기준이 됩니다."
     - 버튼: 일일 마감 입력
  2. 운영 점검 데이터
     - 현재 보유 여부
     - 최근 입력일
     - 목적: "이 데이터는 매장 운영 품질 모니터링에 사용됩니다."
     - 버튼: QSC 입력
  3. 구조 데이터
     - 현재 보유 여부 (메뉴/재료)
     - 목적: "이 데이터는 메뉴 수익 구조 분석의 기준이 됩니다."
     - 버튼: 메뉴/재료 입력
  4. 기준 데이터
     - 현재 보유 여부 (목표)
     - 목적: "이 데이터는 목표 대비 성과 분석의 기준이 됩니다."
     - 버튼: 목표 입력

##### 🟨 ZONE 3: 데이터 자산 완성도
- **제목**: "🏗️ 데이터 자산 완성도"
- **카드 4개** (4열 레이아웃):
  1. 등록 메뉴 (📘)
     - 누락 가격 개수 표시
     - **목적 문구**: "이 데이터는 메뉴 수익 구조 분석의 기준이 됩니다."
  2. 등록 재료 (🧺)
     - 누락 단가 개수 표시
     - **목적 문구**: "이 데이터는 원가 계산과 재료 사용량 분석의 기준이 됩니다."
  3. 레시피 완성도 (🍳)
     - 80% 미만이면 권장 메시지
     - **목적 문구**: "이 데이터가 있어야 적자 메뉴를 구분할 수 있습니다."
  4. 이번 달 목표 (🎯)
     - 설정 여부 표시
     - **목적 문구**: "이 데이터는 목표 대비 성과 분석의 기준이 됩니다."

##### 🟧 ZONE 4: 입력 네비게이션 (시스템 구축 동선)

**🛠 구조 데이터 입력 (설계)** (4열)
- 📘 메뉴 입력
  - 설명: "이 입력은 메뉴 수익 구조 분석의 기준을 만듭니다."
- 🧺 재료 입력
  - 설명: "이 입력은 원가 계산의 기준을 만듭니다."
- 🍳 레시피 입력
  - 설명: "이 입력은 메뉴 수익성 분석의 기준을 만듭니다."
- 📦 재고 입력
  - 설명: "이 입력은 발주 최적화 분석의 기준을 만듭니다."

**⚡ 운영 데이터 입력 (기록)** (3열)
- 📝 오늘 마감 입력
  - 설명: "이 입력은 매출 추이 분석의 데이터를 만듭니다."
- 🩺 QSC 입력
  - 설명: "이 입력은 운영 품질 모니터링의 데이터를 만듭니다."
- 📅 월간 정산 입력
  - 설명: "이 입력은 목표 대비 성과 분석의 데이터를 만듭니다."

**🎯 기준 데이터 입력 (판단)** (2열)
- 🎯 매출 목표 입력
  - 설명: "이 입력은 목표 대비 성과 분석의 기준을 만듭니다."
- 🧾 비용 목표 입력
  - 설명: "이 입력은 비용 최적화 분석의 기준을 만듭니다."

**⚙ 과거 데이터 구축 (초기 세팅)** (Expander)
- 🧮 매출/방문자 입력
  - 설명: "이 입력은 과거 매출 데이터를 구축합니다."
- 📦 판매량 입력
  - 설명: "이 입력은 과거 판매량 데이터를 구축합니다."

#### 4. 버튼 강조 로직
- **Primary 버튼** (파란색 글로우):
  - 오늘 마감 미완료 시
  - 목표 미설정 시
  - 가격/단가 누락 시
  - 레시피 완성도 80% 미만 시
- **Secondary 버튼**: 완료된 항목

#### 5. 컨텐츠 wrapper 종료
- `</div></div>` 닫기

---

## 🔄 페이지 이동 로직

모든 버튼 클릭 시:
```python
st.session_state.current_page = "페이지 키"
st.rerun()
```

**페이지 키 매핑**:
- "일일 입력(통합)"
- "건강검진 실시"
- "실제정산"
- "목표 매출구조"
- "목표 비용구조"
- "메뉴 입력"
- "재료 입력"
- "레시피 등록"
- "재고 입력"
- "매출 등록"
- "판매량 등록"

---

## 🎯 주요 특징

1. **데이터 성숙도 기반 가이드**: 0-100% 점수로 데이터 완성도 표시
2. **우선순위 기반 추천**: 오늘 마감 > QSC > 정산 순서
3. **동적 버튼 강조**: 누락/미완료 항목은 Primary 버튼으로 강조
4. **애니메이션 효과**: 시퀀셜 등장 애니메이션 (delay-1, delay-2, ...)
5. **Ultra Premium 배경**: 고급 배경 레이어 (토글로 제어 가능)
6. **안정성 보장**: 애니메이션 실패해도 컨텐츠는 항상 보임

---

## 📝 개선 이력

- **PHASE 1**: CSS 주입 1회 가드 적용
- **PHASE 2**: 인라인 애니메이션 CSS 분리, backdrop-filter 토글화, prefers-reduced-motion 지원
- **PHASE 3**: CSS Manager 도입 (FX 계층)
- **v4.1**: 시스템 허브화 - ZONE 구조 재편, 시스템 진단 블록 신설, 데이터 지도 리프레이밍
