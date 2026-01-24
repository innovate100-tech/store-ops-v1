# 입력센터 UI 통일 적용 보고서

## 📋 개요

입력센터 하위 11개 페이지의 UI를 통일된 디자인 언어로 정리하기 위한 작업입니다.
2개 레이아웃 타입(FORM형, CONSOLE형) + QSC 별도 유지로 통일합니다.

**작업 일자**: 2026-01-25  
**버전**: v1.1 (보강 완료)  
**상태**: 진행 중 (1단계 완료 + 보강 작업 완료)

---

## 🎯 목표

- 입력센터 11개 페이지가 "같은 제품"처럼 보이는 수준의 타이포/간격/카드/CTA 규격 통일
- 가이드 박스가 페이지 성격에 맞게 다르게 보이되, 컴포넌트 형태는 동일
- 페이지 이동/리런 후에도 깨짐 없음
- 메인 콘텐츠(본문) 다른 페이지에 CSS 영향 없음

---

## 📐 레이아웃 타입 설계

### (A) FORM형 레이아웃
**대상 페이지**: (1,3,4,5,10,11)
- 일일 입력(통합) = 마감입력
- 실제정산 = 월간정산입력
- 목표 매출구조 = 매출목표입력
- 목표 비용구조 = 비용목표입력
- 매출 등록 = 매출방문자입력(보정)
- 판매량 등록 = 판매량입력(보정)

**구성 요소**:
1. Header: 아이콘+제목 + 상태배지(저장됨/임시/마감완료/보정모드 등)
2. GuideBox: 성격별 템플릿(G1/G2/G3 중 선택)
3. Summary Strip: 선택한 날짜/월 + 핵심 숫자 2~4개 + 경고/누락 배지
4. Main Card: 입력 폼
5. ActionBar: Primary 1개 + Secondary 1~2개 (저장/불러오기/리셋 등)

### (B) CONSOLE형 레이아웃
**대상 페이지**: (6,7,8,9)
- 메뉴 입력
- 재료 입력
- 레시피 등록
- 재고 입력

**구성 요소**:
1. Top Dashboard: 현황 KPI + 진행률/알림
2. Work Area: (단일/일괄 입력) 영역을 카드로 정리
3. Filter Bar: 검색/필터 영역을 '한 줄'로 정돈
4. List/Editor: 목록/수정 UI는 카드/테이블 형태 유지하되 타이포/간격/섹션 헤더 통일
5. Bottom: "다음 추천 행동" CTA 1개

### (C) QSC 별도 레이아웃
**대상 페이지**: (2)
- 건강검진 실시 = QSC입력

**구성 요소**:
- 기존 '입력/결과/이력' 탭 구조 유지
- 공통 Header + GuideBox만 상단에 추가해 톤만 맞춤
- 진행률/자동저장 UX는 그대로 유지

---

## 📦 GuideBox 템플릿 3종

### G1: 일일 입력(마감)
- "오늘 입력할 것 / 임시 vs 마감 / 다음에 반영"

### G2: 보정 도구(매출등록/판매량등록)
- "보정 페이지 경고 / 공식반영 조건 / 충돌/우선순위"

### G3: 월간(목표/정산)
- "월 단위 확정 / 목표→실제→성적표 / 확정 후 readonly"

---

## 🛠 구현 내용

### 1. 공통 레이아웃 컴포넌트 생성

**파일**: `src/ui/layouts/input_layouts.py`

**주요 함수**:
- `render_form_layout()`: FORM형 레이아웃 렌더링
- `render_console_layout()`: CONSOLE형 레이아웃 렌더링
- `render_guide_box()`: GuideBox 템플릿 렌더링 (G1/G2/G3)
- `render_action_bar()`: ActionBar 렌더링 (Primary + Secondary)
- `render_summary_strip()`: Summary Strip 렌더링

**CSS 스타일**:
- 페이지별 스코프 적용 (전역 CSS 금지)
- `.ps-input-header`: Header 스타일
- `.ps-guide-box`: GuideBox 스타일 (G1/G2/G3별 색상)
- `.ps-action-bar`: ActionBar 스타일
- `.ps-summary-strip`: Summary Strip 스타일
- `.ps-main-card`: Main Card 스타일
- `.ps-console-*`: CONSOLE형 전용 스타일

### 2. 일일 입력(통합) 페이지 적용

**파일**: `ui_pages/daily_input_hub.py`

**변경 사항**:
- `render_page_header()` 제거 → 레이아웃에서 처리
- 상태 대시보드 제거 → Mini Progress Panel로 대체 (4항목 완료 여부)
- Summary Strip 재정의 → 요약+경고용 (날짜만 간단히)
- GuideBox 추가 (G1 템플릿, 3줄 규격)
- ActionBar 위치 고정 → 폼 상단 고정 위치 (탭 외부)
- 탭 기반 입력을 `render_main_content()` 함수로 감싸기
- 액션 버튼을 `handle_temp_save()`, `handle_close()` 함수로 분리
- `render_form_layout()` 호출로 전체 감싸기

**기존 로직 유지**:
- 모든 위젯 key 그대로 유지
- 모든 저장/로드 함수 그대로 유지
- 모든 계산/검증 로직 그대로 유지

---

## 📝 사용 예시 코드

### FORM형 레이아웃 적용 예시

```python
from src.ui.layouts.input_layouts import render_form_layout

def render_daily_input_hub():
    # ... 데이터 로드 및 상태 확인 ...
    
    # 상태 배지
    status_badge = {"text": "✅ 마감 완료", "type": "success"}
    
    # Summary Strip 항목
    summary_items = [
        {"label": "날짜", "value": "2026-01-25 (월)", "badge": None},
        {"label": "진행률", "value": "3/4", "badge": "warning"},
        {"label": "매출", "value": "1,000,000원", "badge": "success"},
    ]
    
    # Main Content 함수
    def render_main_content():
        # 탭 기반 입력 폼
        tab1, tab2 = st.tabs(["💰 매출", "👥 방문자"])
        with tab1:
            # ... 입력 위젯 ...
    
    # 액션 함수
    def handle_save():
        # ... 저장 로직 ...
    
    def handle_close():
        # ... 마감 로직 ...
    
    # FORM형 레이아웃 적용
    render_form_layout(
        title="오늘 마감 입력",
        icon="📝",
        status_badge=status_badge,
        guide_kind="G1",
        summary_items=summary_items,
        action_primary={
            "label": "📋 마감하기",
            "key": "daily_input_close",
            "action": handle_close
        },
        action_secondary=[
            {
                "label": "💾 임시 저장",
                "key": "daily_input_save",
                "action": handle_save
            }
        ],
        main_content=render_main_content
    )
```

---

## ✅ 완료된 작업

### 1단계: 공통 레이아웃 컴포넌트 생성 ✅
- [x] `src/ui/layouts/input_layouts.py` 생성
- [x] FORM형 레이아웃 함수 구현
- [x] CONSOLE형 레이아웃 함수 구현
- [x] GuideBox 템플릿 3종 구현
- [x] ActionBar 컴포넌트 구현
- [x] Summary Strip 컴포넌트 구현
- [x] CSS 스타일 정의 (페이지별 스코프)

### 2단계: 일일 입력(통합) 페이지 적용 ✅
- [x] FORM형 레이아웃 적용
- [x] Header + 상태 배지 적용
- [x] GuideBox (G1) 적용 (3줄 규격)
- [x] Summary Strip 적용 (요약+경고용)
- [x] Mini Progress Panel 적용 (4항목 완료 여부)
- [x] ActionBar (폼 상단 고정 위치)
- [x] Main Card (탭 기반 입력) 적용
- [x] 기존 로직/위젯 key 유지 확인

### 2-1단계: 보강 작업 ✅
- [x] GuideBox 3줄 규격 통일
- [x] Summary Strip 역할 재정의
- [x] Mini Progress Panel 컴포넌트 추가
- [x] ActionBar 위치 고정 (탭 외부)
- [x] CSS 주입 안정화 (1곳에서 항상 주입)

---

## 🔄 진행 예정 작업

### 3단계: FORM형 나머지 페이지 확장 (순서 변경)
- [ ] 매출 등록 (매출방문자입력) - G2 템플릿
- [ ] 판매량 등록 (판매량입력) - G2 템플릿
- [ ] 목표 비용구조 (비용목표입력) - G3 템플릿
- [ ] 목표 매출구조 (매출목표입력) - G3 템플릿
- [ ] 실제정산 (월간정산입력) - G3 템플릿

### 4단계: CONSOLE형 페이지 적용
- [ ] 메뉴 입력
- [ ] 재료 입력
- [ ] 레시피 등록
- [ ] 재고 입력

### 5단계: QSC 페이지 적용
- [ ] 건강검진 실시 (Header + GuideBox만 추가)

---

## 📁 수정된 파일 목록

### 신규 생성
1. `src/ui/layouts/__init__.py` - 레이아웃 모듈 초기화
2. `src/ui/layouts/input_layouts.py` - 공통 레이아웃 컴포넌트

### 수정
1. `ui_pages/daily_input_hub.py` - FORM형 레이아웃 적용

---

## 🎨 레이아웃 함수 사용 예시

### FORM형 레이아웃

```python
render_form_layout(
    title="페이지 제목",
    icon="📝",
    status_badge={"text": "✅ 상태", "type": "success"},
    guide_kind="G1",  # "G1" | "G2" | "G3" (3줄 규격 자동 적용)
    guide_conclusion=None,  # None이면 기본값 사용
    guide_bullets=None,  # None이면 기본값 사용 (최대 2개)
    guide_next_action=None,  # None이면 기본값 사용
    summary_items=[  # 요약+경고용
        {"label": "날짜", "value": "2026-01-25", "badge": None},
    ],
    mini_progress_items=[  # 4항목 완료 여부 (선택사항)
        {"label": "항목1", "status": "success", "value": "완료"},
        {"label": "항목2", "status": "pending", "value": "진행중"},
    ],
    action_primary={  # 폼 상단 고정 위치
        "label": "저장",
        "key": "save_button",
        "action": lambda: save_function()
    },
    action_secondary=[
        {
            "label": "리셋",
            "key": "reset_button",
            "action": lambda: reset_function()
        }
    ],
    main_content=lambda: render_input_form()  # ActionBar는 탭 외부에 표시됨
)
```

### CONSOLE형 레이아웃

```python
render_console_layout(
    title="페이지 제목",
    icon="📊",
    dashboard_content=lambda: render_dashboard(),
    work_area_content=lambda: render_input_area(),
    filter_content=lambda: render_filters(),
    list_content=lambda: render_list(),
    cta_label="다음 추천 행동",
    cta_action=lambda: handle_cta()
)
```

---

## ⚠️ 주의사항

### 절대 금지
- 기능/로직/DB/계산/저장 우선순위 변경 금지
- 입력 위젯 key/name 변경 금지
- JS/DOM 조작 금지
- 전역 CSS 금지 (메인 콘텐츠/다른 페이지 영향 금지)

### 필수 준수
- 기존 로직은 그대로 유지
- 화면 구성만 레이아웃 함수로 감싸기
- 위젯 key는 절대 변경하지 않기
- CSS는 페이지별 스코프 내에서만 적용

---

## 📊 적용 전/후 비교

### 적용 전
- 각 페이지마다 다른 스타일
- 일관성 없는 레이아웃
- 가이드/안내 메시지 형식 불일치

### 적용 후 (예상)
- 통일된 Header + GuideBox + Summary Strip
- 일관된 ActionBar 배치
- 동일한 타이포/간격/카드 스타일
- 페이지 성격에 맞는 GuideBox 템플릿

---

## 🔍 검증 체크리스트

- [x] 공통 레이아웃 컴포넌트 생성 완료
- [x] 일일 입력(통합) 페이지 적용 완료
- [ ] 페이지 이동/리런 후 CSS 유지 확인
- [ ] 메인 콘텐츠 다른 페이지 영향 없음 확인
- [ ] 모든 위젯 key 변경 없음 확인
- [ ] 기존 로직 정상 작동 확인

---

## 📝 다음 단계

1. **일일 입력(통합) 페이지 테스트**
   - 레이아웃 적용 확인
   - 기능 정상 작동 확인
   - CSS 유지 확인

2. **FORM형 나머지 페이지 확장 (순서 변경)**
   - 매출 등록 (G2) ← 우선
   - 판매량 등록 (G2)
   - 목표 비용구조 (G3)
   - 목표 매출구조 (G3)
   - 실제정산 (G3)

3. **CONSOLE형 페이지 적용**
   - 메뉴 입력부터 시작
   - 재료/레시피/재고 순차 적용

4. **QSC 페이지 적용**
   - Header + GuideBox만 추가

---

---

## 🔧 v1.1 보강 작업 (2026-01-25)

### 주요 변경사항

1. **Summary Strip 역할 재정의** ✅
   - 진행률 대시보드 대체가 아니라 '요약+경고'용으로 변경
   - 일일 입력(통합)은 기존 진행률 정보를 Main Card 위에 "Mini Progress Panel"로 표시
   - 4항목(매출/방문자/판매량/메모) 완료 여부만 표시

2. **ActionBar 위치 고정** ✅
   - 탭 내부가 아니라 폼 상단 고정 위치로 변경
   - FORM형 모든 페이지에서 탭/섹션과 무관하게 항상 상단에 표시

3. **GuideBox 3줄 규격 통일** ✅
   - "결론 1줄 + bullet 2개 + 다음 행동 1줄" 규격으로 통일
   - G1/G2/G3 템플릿 모두 이 규격으로 재작성
   - 가독성 향상

4. **CSS 주입 안정화** ✅
   - 공통 레이아웃 CSS(ps-*)는 rerun마다 깨지지 않도록 1곳에서 항상 주입
   - `render_form_layout()`에서 CSS 주입, 하위 컴포넌트는 중복 주입 방지
   - 페이지별 CSS 최소화, 공통 클래스 재사용 최우선

5. **Mini Progress Panel 컴포넌트 추가** ✅
   - 4항목 완료 여부를 시각적으로 표시
   - status: "success" | "pending" | "none"
   - Main Card 위에 표시

### 다음 적용 순서 (변경)

1. 매출 등록 (G2 템플릿)
2. 판매량 등록 (G2 템플릿)
3. 목표 비용구조 (G3 템플릿)
4. 목표 매출구조 (G3 템플릿)
5. 실제정산 (G3 템플릿)

---

**작성일**: 2026-01-25  
**버전**: v1.1  
**상태**: 1단계 완료 + 보강 작업 완료 (공통 컴포넌트 생성 + 일일 입력 적용 + 보강)
