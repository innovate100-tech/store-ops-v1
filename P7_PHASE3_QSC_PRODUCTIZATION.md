# Phase 3: QSC 입력 페이지 제품화 보고서

## 작업 개요
- **대상 파일**: `ui_pages/health_check/health_check_page.py`
- **작업 일자**: 2026-01-25
- **목표**: QSC 페이지를 다른 입력 페이지와 동일한 "입력 도구" 톤으로 통일

## 구현 내용

### 1. FormKit v2 스코프 주입
- ✅ `inject_form_kit_css()` 추가
- ✅ `inject_form_kit_v2_css("health_check_page")` 적용
- ✅ `data-ps-scope="health_check_page"` 기반 CSS 스코프 유지

### 2. "체크(입력)" 탭 구조 개편
- ✅ `render_form_layout` 적용하여 FORM형 레이아웃 통일
- ✅ 전체를 `ps_input_block` 리듬으로 재구성
- ✅ 질문 묶음을 영역별 블록 단위로 그룹화
- ✅ 필터는 Secondary 블록으로 구성
- ✅ 상태 메시지는 `ps_inline_feedback` 사용
- ✅ 진행률은 Summary Strip + Mini Progress Panel로 표시

### 3. Header + GuideBox + Summary Strip 유지
- ✅ `render_form_layout` 내부에서 Header 자동 렌더링
- ✅ GuideBox는 "입력 도구 / 운영 점검" 성격으로 조정
  - 결론: "9개 영역(Q, S, C, P1, P2, P3, M, H, F)에 대해 각 10문항씩 총 90문항을 답변하세요"
  - Bullets: 자동 저장 안내, 최소 60개 문항 필요
  - 다음 행동: "완료 후 결과 리포트에서 상세 분석을 확인하세요"

### 4. 결과 / 이력 탭 처리
- ✅ 기능 유지
- ✅ 상단 안내 문구 개선: "📊 분석센터로 이전 예정 (현재는 참고용)"
- ✅ 입력 컴포넌트로 오해될 수 있는 요소 제거 (기존 구조 유지)

### 5. CTA 규칙
- ✅ 탭 내부 저장/완료 버튼 제거
- ✅ `render_form_layout` ActionBar 1곳만 사용
- ✅ Primary: "✅ 체크 완료" (완료 가능 시) / "⏳ 완료 불가" (불가 시)
- ✅ Secondary: "💾 수동 저장" (dirty 있을 때만), "🔄 초기화"

### 6. 검증 결과

#### 위젯 key 변경 없음 확인
다음 key들이 모두 유지됨:
- `qsc_category_filter`: 영역 필터
- `qsc_search`: 질문 검색
- `qsc_btn_{session_id}_{category}_{question_code}_{raw_value}`: 질문 답변 버튼
- `health_check_complete`: 완료 버튼
- `health_check_manual_save`: 수동 저장 버튼
- `health_check_reset`: 초기화 버튼

#### ActionBar 1곳만 사용 확인
- `render_form_layout` 내부에서 ActionBar 1곳만 렌더링
- 탭 내부에 별도 저장/완료 버튼 없음

#### CSS 유지 확인
- `inject_form_kit_v2_css("health_check_page")` 적용
- `data-ps-scope="health_check_page"` 기반 스코프 유지

## 변경 파일
- `ui_pages/health_check/health_check_page.py`

## 주요 변경 사항

### Import 추가
```python
from src.ui.layouts.input_layouts import render_form_layout
from src.ui.components.form_kit import inject_form_kit_css
from src.ui.components.form_kit_v2 import (
    inject_form_kit_v2_css,
    ps_input_block,
    ps_secondary_select,
    ps_inline_feedback,
    ps_input_status_badge
)
```

### render_health_check_page() 변경
- 기존: 수동 Header + GuideBox 렌더링
- 변경: FormKit v2 CSS 주입만 수행 (나머지는 render_form_layout에서 처리)

### render_input_form_redesigned() 재구성
- 기존: 수동 섹션 헤더 + 버튼 배치
- 변경: `render_form_layout` + `ps_input_block` 리듬 적용
  - Summary Strip: 전체 문항, 완료 문항, 완료율
  - Mini Progress Panel: 영역별 진행률 (최대 4개)
  - 필터 블록: Secondary 블록으로 구성
  - 질문 입력 블록: 영역별로 그룹화하여 Secondary 블록으로 구성
  - ActionBar: 완료/저장/초기화 버튼

## 기능/로직 변경 없음 확인
- ✅ DB 저장/로드 로직 유지
- ✅ 계산 로직 유지
- ✅ 상태 관리 로직 유지
- ✅ 결과/이력 탭 기능 유지

## 다음 단계
Phase 4: 입력센터 통합 스모크 테스트 진행
