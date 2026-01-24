# 입력센터 UI 통일 적용 보고서

## 📋 개요

입력센터 하위 11개 페이지의 UI를 통일된 디자인 언어로 정리하기 위한 작업입니다.
2개 레이아웃 타입(FORM형, CONSOLE형) + QSC 별도 유지로 통일합니다.

**작업 일자**: 2026-01-25  
**버전**: v1.0  
**상태**: 진행 중 (1단계 완료)

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
- 상태 대시보드 제거 → Summary Strip로 대체
- GuideBox 추가 (G1 템플릿)
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
- [x] GuideBox (G1) 적용
- [x] Summary Strip 적용
- [x] Main Card (탭 기반 입력) 적용
- [x] ActionBar (임시 저장 + 마감하기) 적용
- [x] 기존 로직/위젯 key 유지 확인

---

## 🔄 진행 예정 작업

### 3단계: FORM형 나머지 페이지 확장
- [ ] 실제정산 (월간정산입력) - G3 템플릿
- [ ] 목표 매출구조 (매출목표입력) - G3 템플릿
- [ ] 목표 비용구조 (비용목표입력) - G3 템플릿
- [ ] 매출 등록 (매출방문자입력) - G2 템플릿
- [ ] 판매량 등록 (판매량입력) - G2 템플릿

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
    guide_kind="G1",  # "G1" | "G2" | "G3"
    guide_bullets=None,  # None이면 기본값 사용
    guide_warnings=None,
    summary_items=[
        {"label": "항목1", "value": "값1", "badge": "success"},
        {"label": "항목2", "value": "값2", "badge": None},
    ],
    action_primary={
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
    main_content=lambda: render_input_form()
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

2. **FORM형 나머지 페이지 확장**
   - 실제정산 (G3)
   - 목표 매출구조 (G3)
   - 목표 비용구조 (G3)
   - 매출 등록 (G2)
   - 판매량 등록 (G2)

3. **CONSOLE형 페이지 적용**
   - 메뉴 입력부터 시작
   - 재료/레시피/재고 순차 적용

4. **QSC 페이지 적용**
   - Header + GuideBox만 추가

---

**작성일**: 2026-01-25  
**버전**: v1.0  
**상태**: 1단계 완료 (공통 컴포넌트 생성 + 일일 입력 적용)
