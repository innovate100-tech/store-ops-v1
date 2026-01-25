# 입력센터 완전 정리 보고서

## 작업 개요
- **작업 일자**: 2026-01-25
- **목적**: 입력센터 메인 페이지와 하위 페이지들의 전체 구조 및 관계 정리
- **대상**: 입력센터 전체 (메인 허브 + 11개 하위 페이지)

---

## 1. 입력센터 전체 구조

### 1.1 계층 구조

```
입력센터 (Input Center)
│
├── 📍 메인 허브: 데이터 입력 센터 (input_hub.py)
│   └── 하위 페이지로의 네비게이션 허브
│
└── 📄 하위 입력 페이지 (11개)
    │
    ├── FORM형 (6개)
    │   ├── daily_input_hub (일일 입력 통합)
    │   ├── sales_entry (매출 등록)
    │   ├── sales_volume_entry (판매량 등록)
    │   ├── target_cost_structure (목표 비용구조)
    │   ├── target_sales_structure (목표 매출구조)
    │   └── settlement_actual (실제정산)
    │
    ├── CONSOLE형 (4개)
    │   ├── menu_input (메뉴 입력)
    │   ├── ingredient_input (재료 입력)
    │   ├── recipe_management (레시피 관리)
    │   └── inventory_input (재고 입력)
    │
    └── QSC (1개)
        └── health_check_page (건강검진 실시)
```

---

## 2. 메인 허브: 데이터 입력 센터

### 2.1 파일 정보
- **파일**: `ui_pages/input/input_hub.py`
- **함수**: `render_input_hub_v3()`
- **페이지 키**: `"입력 허브"` (app.py 라우팅)
- **제목**: "✍ 데이터 입력 센터"

### 2.2 페이지 구조

#### [1] 통합 가이드 카드
- **목적**: 데이터 성숙도(Maturity Level) 표시
- **내용**:
  - 데이터 자산 가이드 안내
  - 성숙도 점수 (0-100%)
  - 성숙도 진행률 바
  - 상태 메시지 (PREMIUM / 미완료 데이터 보완 권장)

**성숙도 점수 계산 기준**:
- 메뉴 등록 완료 (가격 누락 없음): +25점
- 재료 등록 완료 (단가 누락 없음): +25점
- 레시피 완성도 80% 이상: +25점
- 이번 달 목표 설정 완료: +25점

#### [2] 관제 보드: 오늘의 입력 현황
- **목적**: 오늘 입력해야 할 항목들의 현황 확인
- **구성**:
  1. **오늘의 마감** (Priority 1)
     - 상태: 완료 / 미완료
     - 요약: 매출액 / 방문자 수
     - 버튼: "📝 오늘 마감 입력" → `일일 입력(통합)`
  
  2. **정기 QSC 점검** (Priority 4)
     - 상태: 완료 / 권장
     - 요약: 최근 완료 날짜
     - 버튼: "🩺 QSC 입력" → `건강검진 실시`
  
  3. **이번 달 정산** (Priority 5)
     - 상태: 완료 / 대기
     - 요약: 현재 월
     - 버튼: "📅 월간 정산 입력" → `실제정산`

#### [3] 자산 구축 현황: 입력 데이터 완성도
- **목적**: 입력된 데이터의 완성도 확인 및 누락 항목 파악
- **구성**:
  1. **등록 메뉴**
     - 값: 등록된 메뉴 개수
     - 경고: 가격 누락 개수 표시
     - 버튼: "📘 메뉴 입력" → `메뉴 입력`
  
  2. **등록 재료**
     - 값: 등록된 재료 개수
     - 경고: 단가 누락 개수 표시
     - 버튼: "🧺 재료 입력" → `재료 입력`
  
  3. **레시피 완성도**
     - 값: 레시피 완성도 (%)
     - 경고: 80% 미만 시 권장 메시지
     - 버튼: "🍳 레시피 입력" → `레시피 등록`
  
  4. **이번 달 목표**
     - 값: 설정 완료 / 미설정
     - 경고: 미설정 시 목표 설정 필요
     - 버튼: "🎯 매출 목표 입력" / "🧾 비용 목표 입력"

#### [4] 정기 입력 작업
- **섹션 제목**: "⚡ 정기 입력 작업"
- **설명**: 정기적으로 입력해야 하는 핵심 데이터
- **버튼**:
  1. **📝 오늘 마감 입력** → `일일 입력(통합)`
     - 상태에 따라 Primary/Secondary 버튼 타입 변경
  2. **🩺 QSC 입력** → `건강검진 실시`
  3. **📅 월간 정산 입력** → `실제정산`

#### [5] 목표 입력
- **섹션 제목**: "🎯 목표 입력"
- **설명**: 분석 기준이 될 목표를 입력합니다. 누락 시 파란색으로 강조됩니다.
- **버튼**:
  1. **🎯 매출 목표 입력** → `목표 매출구조`
     - 목표 미설정 시 Primary 버튼 + "(필수)" 표시
  2. **🧾 비용 목표 입력** → `목표 비용구조`

#### [6] 기초 데이터 입력
- **섹션 제목**: "🛠️ 기초 데이터 입력"
- **설명**: 메뉴, 재료 등 기초 데이터를 입력합니다. 누락 발견 시 파란색으로 강조됩니다.
- **버튼**:
  1. **📘 메뉴 입력** → `메뉴 입력`
     - 가격 누락 시 Primary 버튼 + 누락 개수 표시
  2. **🧺 재료 입력** → `재료 입력`
     - 단가 누락 시 Primary 버튼 + 누락 개수 표시
  3. **🍳 레시피 입력** → `레시피 등록`
     - 레시피 완성도 80% 미만 시 Primary 버튼
  4. **📦 재고 입력** → `재고 입력`

#### [7] 과거 데이터 입력
- **섹션 제목**: "⚙️ 과거 데이터 입력" (Expander)
- **설명**: 과거 데이터 입력 및 보정 도구
- **버튼**:
  1. **🧮 매출/방문자 입력** → `매출 등록`
  2. **📦 판매량 입력** → `판매량 등록`

### 2.3 네비게이션 메커니즘

**라우팅 방식**:
```python
# 버튼 클릭 시
st.session_state.current_page = "페이지 키"
st.rerun()
```

**페이지 키 매핑** (app.py):
- `"일일 입력(통합)"` → `daily_input_hub.py`
- `"매출 등록"` → `sales_entry.py`
- `"판매량 등록"` → `sales_volume_entry.py`
- `"목표 비용구조"` → `target_cost_structure.py`
- `"목표 매출구조"` → `target_sales_structure.py`
- `"실제정산"` → `settlement_actual.py`
- `"메뉴 입력"` → `menu_input.py`
- `"재료 입력"` → `ingredient_input.py`
- `"레시피 등록"` → `recipe_management.py`
- `"재고 입력"` → `inventory_input.py`
- `"건강검진 실시"` → `health_check_page.py`

### 2.4 동적 상태 표시

**Primary 버튼 강조 조건**:
- 오늘 마감 미완료 시
- 목표 미설정 시
- 메뉴 가격 누락 시
- 재료 단가 누락 시
- 레시피 완성도 80% 미만 시

**상태 카드 색상**:
- `completed`: 초록색 (#10B981)
- `warning`: 주황색 (#F59E0B)
- `pending`: 회색 (#94A3B8)

---

## 3. 하위 입력 페이지 상세

### 3.1 FORM형 페이지 (6개)

#### 3.1.1 daily_input_hub (일일 입력 통합)
- **파일**: `ui_pages/daily_input_hub.py`
- **함수**: `render_daily_input_hub()`
- **레이아웃**: FORM형 (`render_form_layout`)
- **FormKit v2 스코프**: `"daily_input_hub"`
- **주요 기능**:
  - 날짜별 매출/방문자/판매량/메모 입력
  - 탭 구조로 입력 항목 구분
  - 임시 저장 / 마감 완료 ActionBar
  - 진행 상황 Mini Progress Panel
- **입력 항목**:
  - 매출 (카드/현금)
  - 네이버 방문자
  - 메뉴별 판매량
  - 메모
- **ActionBar**:
  - Primary: "💾 임시 저장" / "✅ 마감 완료"
  - Secondary: 없음

#### 3.1.2 sales_entry (매출 등록)
- **파일**: `ui_pages/sales_entry.py`
- **함수**: `render_sales_entry()`
- **레이아웃**: FORM형 (`render_form_layout`)
- **FormKit v2 스코프**: `"sales_entry"`
- **주요 기능**:
  - 단일/일괄 모드 선택
  - 날짜별 매출 입력
  - Summary Strip으로 입력 상태 확인
- **입력 항목**:
  - 날짜
  - 카드 매출
  - 현금 매출
  - 방문자 (선택)
- **ActionBar**:
  - Primary: "💾 저장"
  - Secondary: 없음

#### 3.1.3 sales_volume_entry (판매량 등록)
- **파일**: `ui_pages/sales_volume_entry.py`
- **함수**: `render_sales_volume_entry()`
- **레이아웃**: FORM형 (`render_form_layout`)
- **FormKit v2 스코프**: `"sales_volume_entry"`
- **주요 기능**:
  - 날짜별 메뉴별 판매량 입력
  - 메뉴별 블록으로 구분
  - Summary Strip으로 진행 상황 확인
- **입력 항목**:
  - 날짜
  - 메뉴별 판매량
- **ActionBar**:
  - Primary: "💾 저장"
  - Secondary: 없음

#### 3.1.4 target_cost_structure (목표 비용구조)
- **파일**: `ui_pages/target_cost_structure.py`
- **함수**: `render_target_cost_structure()`
- **레이아웃**: FORM형 (`render_form_layout`)
- **FormKit v2 스코프**: `"target_cost_structure"`
- **주요 기능**:
  - 기간 선택 (연/월)
  - 카테고리별 비용 목표 입력
  - 항목 추가/삭제
  - Summary Strip으로 목표 요약
- **입력 항목**:
  - 기간 (연/월)
  - 카테고리별 비용 (금액/비율)
- **ActionBar**:
  - Primary: "💾 목표 저장" / "💾 저장 (수정)"
  - Secondary: "📋 전월 데이터 복사"

#### 3.1.5 target_sales_structure (목표 매출구조)
- **파일**: `ui_pages/target_sales_structure.py`
- **함수**: `render_target_sales_structure()`
- **레이아웃**: FORM형 (`render_form_layout`)
- **FormKit v2 스코프**: `"target_sales_structure"`
- **주요 기능**:
  - 기간 선택 (연/월)
  - 메뉴별 목표 매출 입력
  - 항목 추가/삭제
  - Summary Strip으로 목표 요약
- **입력 항목**:
  - 기간 (연/월)
  - 메뉴별 목표 매출
- **ActionBar**:
  - Primary: "💾 목표 저장"
  - Secondary: 없음

#### 3.1.6 settlement_actual (실제정산)
- **파일**: `ui_pages/settlement_actual.py`
- **함수**: `render_settlement_actual()`
- **레이아웃**: FORM형 (`render_form_layout`)
- **FormKit v2 스코프**: `"settlement_actual"`
- **주요 기능**:
  - 기간 선택 (연/월)
  - 카테고리별 실제 비용 입력
  - 템플릿 저장/불러오기
  - 항목 추가/삭제
  - Summary Strip으로 정산 요약
  - 구조 리포트 섹션 (참고용)
- **입력 항목**:
  - 기간 (연/월)
  - 카테고리별 실제 비용 (금액/비율)
- **ActionBar**:
  - Primary: "💾 저장"
  - Secondary: "📋 템플릿 저장" / "📂 템플릿 불러오기" / "📋 전월 복사"

### 3.2 CONSOLE형 페이지 (4개)

#### 3.2.1 menu_input (메뉴 입력)
- **파일**: `ui_pages/input/menu_input.py`
- **함수**: `render_menu_input_page()`
- **레이아웃**: CONSOLE형 (`render_console_layout`)
- **FormKit v2 스코프**: `"menu_input"`
- **주요 기능**:
  - 대시보드: 메뉴 현황 요약
  - 입력 영역: 메뉴 추가
  - 목록: 메뉴 목록 및 수정/삭제
  - 필터/검색: 메뉴 찾기
- **입력 항목**:
  - 메뉴명
  - 판매가
  - 카테고리
  - 상태 (판매중/판매중지)
- **ActionBar** (Bottom CTA):
  - Primary: "💾 단일 저장" / "💾 일괄 저장"
  - Secondary: 없음

#### 3.2.2 ingredient_input (재료 입력)
- **파일**: `ui_pages/input/ingredient_input.py`
- **함수**: `render_ingredient_input_page()`
- **레이아웃**: CONSOLE형 (`render_console_layout`)
- **FormKit v2 스코프**: `"ingredient_input"`
- **주요 기능**:
  - 대시보드: 재료 현황 요약
  - 입력 영역: 재료 추가
  - 목록: 재료 목록 및 수정/삭제
  - 필터/검색: 재료 찾기
- **입력 항목**:
  - 재료명
  - 단위
  - 단가
  - 발주 단위 (선택)
  - 변환 비율 (선택)
- **ActionBar** (Bottom CTA):
  - Primary: "💾 단일 저장" / "💾 일괄 저장"
  - Secondary: 없음

#### 3.2.3 recipe_management (레시피 관리)
- **파일**: `ui_pages/recipe_management.py`
- **함수**: `render_recipe_management()`
- **레이아웃**: CONSOLE형 (`render_console_layout`)
- **FormKit v2 스코프**: `"recipe_management"`
- **주요 기능**:
  - 대시보드: 레시피 현황 요약
  - 입력 영역: 레시피 추가
  - 목록: 레시피 목록 및 수정/삭제
  - 필터: 메뉴별 필터
- **입력 항목**:
  - 메뉴 선택
  - 재료 선택
  - 사용량
- **ActionBar** (Bottom CTA):
  - Primary: "💾 저장"
  - Secondary: 없음

#### 3.2.4 inventory_input (재고 입력)
- **파일**: `ui_pages/input/inventory_input.py`
- **함수**: `render_inventory_input_page()`
- **레이아웃**: CONSOLE형 (`render_console_layout`)
- **FormKit v2 스코프**: `"inventory_input"`
- **주요 기능**:
  - 대시보드: 재고 현황 요약
  - 입력 영역: 재고 추가
  - 목록: 재고 목록 및 수정/삭제
  - 필터/검색: 재고 찾기
- **입력 항목**:
  - 재료 선택
  - 현재고
  - 안전재고 (선택)
- **ActionBar** (Bottom CTA):
  - Primary: "💾 변경 저장" / "💾 전체 저장"
  - Secondary: 없음

### 3.3 QSC 페이지 (1개)

#### 3.3.1 health_check_page (건강검진 실시)
- **파일**: `ui_pages/health_check/health_check_page.py`
- **함수**: `render_health_check_page()`
- **레이아웃**: FORM형 (`render_form_layout`)
- **FormKit v2 스코프**: `"health_check_page"`
- **주요 기능**:
  - 9개 영역(Q, S, C, P1, P2, P3, M, H, F) 질문 입력
  - 총 90개 문항 답변
  - 진행 상황 대시보드
  - 필터/검색
  - 결과/이력 탭 (참고용)
- **입력 항목**:
  - 질문별 답변 (예/애매함/아니다)
- **ActionBar**:
  - Primary: "✅ 체크 완료" / "⏳ 완료 불가"
  - Secondary: "💾 수동 저장" (dirty 있을 때만), "🔄 초기화"

---

## 4. 입력센터와 하위 페이지 관계

### 4.1 네비게이션 흐름

```
사이드바 "✍ 입력" 그룹
│
├── [메인] 데이터 입력 센터 (입력 허브)
│   │
│   ├── [정기 입력] → daily_input_hub
│   ├── [정기 입력] → health_check_page
│   ├── [정기 입력] → settlement_actual
│   │
│   ├── [목표 입력] → target_sales_structure
│   ├── [목표 입력] → target_cost_structure
│   │
│   ├── [기초 데이터] → menu_input
│   ├── [기초 데이터] → ingredient_input
│   ├── [기초 데이터] → recipe_management
│   ├── [기초 데이터] → inventory_input
│   │
│   └── [과거 데이터] → sales_entry
│   └── [과거 데이터] → sales_volume_entry
│
└── [하위] 각 입력 페이지 (사이드바에서 직접 접근 가능)
```

### 4.2 데이터 흐름

#### 입력 허브 → 하위 페이지
1. **상태 확인**: 입력 허브에서 각 페이지의 완료 상태 확인
2. **우선순위 표시**: 미완료 항목을 Primary 버튼으로 강조
3. **네비게이션**: 버튼 클릭 시 `st.session_state.current_page` 설정 후 `st.rerun()`

#### 하위 페이지 → 입력 허브
- 사이드바에서 "입력 허브" 클릭으로 복귀
- 각 하위 페이지는 독립적으로 동작 (입력 허브 의존성 없음)

### 4.3 공통 컴포넌트

#### FormKit v2
- **CSS 주입**: 모든 페이지에서 `inject_form_kit_v2_css("page_id")` 사용
- **스코프 격리**: `data-ps-scope="page_id"` 기반으로 페이지별 CSS 격리
- **컴포넌트**:
  - `ps_input_block`: 입력 블록 리듬
  - `ps_primary_money_input`: Primary 금액 입력
  - `ps_primary_quantity_input`: Primary 수량 입력
  - `ps_primary_ratio_input`: Primary 비율 입력
  - `ps_secondary_select`: Secondary 선택 입력
  - `ps_inline_feedback`: 인라인 피드백
  - `ps_input_status_badge`: 입력 상태 배지

#### 레이아웃 시스템
- **FORM형**: `render_form_layout` 사용
  - Header + GuideBox + Summary Strip
  - ActionBar (1곳만)
  - Main Content (ps_input_block 리듬)
- **CONSOLE형**: `render_console_layout` 사용
  - Header
  - Dashboard
  - Work Area
  - List/Editor
  - Bottom CTA

### 4.4 상태 관리

#### 입력 허브 상태 확인 함수
- `_get_today_recommendations()`: 오늘의 추천 항목 확인
- `_get_asset_readiness()`: 자산 구축 현황 확인
- `_count_completed_checklists_last_n_days()`: QSC 완료 횟수 확인
- `_is_current_month_settlement_done()`: 이번 달 정산 완료 여부 확인

#### 하위 페이지 상태
- 각 페이지는 독립적인 상태 관리
- `st.session_state`를 통한 입력 값 관리
- DB 저장/로드는 각 페이지에서 독립적으로 처리

---

## 5. 입력센터 UX 원칙

### 5.1 입력 도구 톤 통일
- 모든 입력 페이지는 "입력 도구" 톤으로 통일
- 분석/전략 요소는 "참고용" 톤으로만 표시

### 5.2 FormKit v2 + 블록 리듬
- 모든 입력 페이지에 FormKit v2 스코프 적용
- `ps_input_block` 리듬으로 입력 항목 그룹화
- Primary 입력: 크고 명확하게 (56px, 22px)
- Secondary 입력: compact하게 (40px, 14px)

### 5.3 ActionBar 1곳만 사용
- 페이지당 ActionBar는 1곳만 존재
- FORM형: `render_form_layout` 내부 ActionBar
- CONSOLE형: `render_console_layout` cta
- 중간 저장 버튼 금지 (CONSOLE형 항목별 수정 저장은 허용)

### 5.4 Summary Strip + Mini Progress Panel
- Summary Strip: 핵심 요약 정보 표시
- Mini Progress Panel: 완료 항목 수 표시 (선택적)

### 5.5 블록 순서
- 위에서 아래로 자연스러운 흐름
- 필터 → 입력 → 저장 순서

### 5.6 입력 밀도
- Primary 입력: 크고 명확하게
- Secondary 입력: compact하게
- 블록 간격: 적절한 여백 유지 (margin-bottom 16px)

### 5.7 추가/삭제 UX
- 항목 추가: 블록 하단 "➕ 추가" 버튼
- 항목 삭제: 항목별 "🗑️" 버튼
- ActionBar로 이동 금지

### 5.8 위젯 key 관리
- 위젯 key는 절대 변경하지 않음
- 페이지별 고유 key 패턴 사용

---

## 6. 입력센터 워크플로우

### 6.1 신규 사용자 워크플로우

```
1. 입력 허브 진입
   ↓
2. 데이터 성숙도 확인 (0%)
   ↓
3. 기초 데이터 입력 (Primary 강조)
   ├── 메뉴 입력
   ├── 재료 입력
   ├── 레시피 입력
   └── 재고 입력
   ↓
4. 목표 입력 (Primary 강조)
   ├── 매출 목표 입력
   └── 비용 목표 입력
   ↓
5. 정기 입력 시작
   ├── 오늘 마감 입력
   ├── QSC 입력
   └── 월간 정산 입력
```

### 6.2 일일 운영 워크플로우

```
1. 입력 허브 진입
   ↓
2. 오늘의 입력 현황 확인
   ↓
3. 오늘 마감 입력 (Primary 강조)
   ├── 매출 입력
   ├── 방문자 입력
   ├── 판매량 입력
   └── 메모 입력
   ↓
4. 마감 완료
```

### 6.3 월간 운영 워크플로우

```
1. 입력 허브 진입
   ↓
2. 이번 달 정산 확인
   ↓
3. 월간 정산 입력
   ├── 카테고리별 실제 비용 입력
   └── 저장
   ↓
4. 목표 대비 성적표 확인
```

---

## 7. 입력센터 데이터 구조

### 7.1 입력 데이터 카테고리

#### 일일 데이터
- `daily_input_hub`: 매출, 방문자, 판매량, 메모
- `sales_entry`: 과거 매출/방문자 보정
- `sales_volume_entry`: 과거 판매량 보정

#### 월간 데이터
- `settlement_actual`: 실제 정산 비용
- `target_cost_structure`: 목표 비용 구조
- `target_sales_structure`: 목표 매출 구조

#### 기초 데이터
- `menu_input`: 메뉴 마스터
- `ingredient_input`: 재료 마스터
- `recipe_management`: 레시피 (메뉴-재료 매핑)
- `inventory_input`: 재고 현황

#### QSC 데이터
- `health_check_page`: 매장 체크리스트 (9개 영역, 90개 문항)

### 7.2 데이터 의존성

```
기초 데이터
├── 메뉴 마스터
│   └── 레시피 (메뉴-재료 매핑)
├── 재료 마스터
│   └── 레시피 (메뉴-재료 매핑)
└── 재고 (재료 기반)

일일 데이터
├── 매출 (독립)
├── 방문자 (독립)
└── 판매량 (메뉴 마스터 기반)

월간 데이터
├── 실제 정산 (독립)
├── 목표 비용 (독립)
└── 목표 매출 (메뉴 마스터 기반)

QSC 데이터
└── 건강검진 (독립)
```

---

## 8. 입력센터 접근 경로

### 8.1 사이드바 접근
- **카테고리**: "✍ 입력"
- **메인**: "데이터 입력센터" (입력 허브)
- **하위**: Expander "상세 선택" 내부
  - 오늘 마감
  - 매출·방문자
  - 판매량
  - 월간 정산
  - 목표(비용)
  - 목표(매출)
  - QSC 체크

### 8.2 입력 허브 접근
- 사이드바 "데이터 입력센터" 클릭
- 각 하위 페이지에서 사이드바로 복귀

### 8.3 하위 페이지 직접 접근
- 사이드바 "상세 선택" Expander에서 직접 접근 가능
- 입력 허브 버튼 클릭으로 접근 가능

---

## 9. 입력센터 특징 요약

### 9.1 통합성
- 모든 입력 기능을 하나의 허브에서 관리
- 상태 확인 및 우선순위 표시로 입력 가이드 제공

### 9.2 일관성
- FormKit v2 + 블록 리듬으로 통일된 UI
- ActionBar 1곳만 사용으로 일관된 UX

### 9.3 지능성
- 데이터 성숙도 점수로 완성도 파악
- 미완료 항목 자동 강조 (Primary 버튼)
- 오늘의 입력 현황 실시간 확인

### 9.4 확장성
- 페이지별 독립적인 상태 관리
- 스코프 기반 CSS 격리로 충돌 방지
- 위젯 key 패턴으로 유지보수 용이

---

## 10. 결론

입력센터는 다음과 같은 구조로 구성되어 있습니다:

1. **메인 허브**: 데이터 입력 센터 (input_hub.py)
   - 통합 가이드 및 상태 확인
   - 하위 페이지로의 네비게이션
   - 동적 우선순위 표시

2. **하위 페이지**: 11개 입력 페이지
   - FORM형 6개: 일일/월간 데이터 입력
   - CONSOLE형 4개: 기초 데이터 관리
   - QSC 1개: 매장 체크리스트

3. **공통 시스템**:
   - FormKit v2 컴포넌트 시스템
   - 레이아웃 시스템 (FORM형/CONSOLE형)
   - 블록 리듬 시스템

입력센터는 하나의 완성된 제품처럼 통일된 UX를 제공하며, 사용자가 쉽게 데이터를 입력하고 관리할 수 있는 구조로 설계되었습니다.

---

**작성일**: 2026-01-25
**버전**: 1.0
