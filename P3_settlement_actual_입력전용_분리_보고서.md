# P3: settlement_actual.py 입력 전용 페이지 역할 분리 보고서

## 작업 목표
'월간 정산' 페이지를 "입력 전용 페이지"로 역할 분리
- 작성/수정/저장/확정만 담당
- 분석/전략 요소 제거

## 제거한 섹션 목록

### 1. 구조 판결 섹션 전체
**위치**: `_render_structure_report_section()` 호출 (1521줄)
**제거 내용**:
- 이번 달 구조 판결 헤더
- 구조 상태 요약 테이블 (4개 구조 점수/상태/요약)
- 이번 달 최우선 과제 (verdict card)
- 지난달 대비 변화 (점수 변화/상태 변화 테이블)
- 다음달 추천 과제 (전략 이동 버튼들)
- 이번 달 구조 판결 확인 완료 처리 버튼

**함수 유지**: `_render_structure_report_section()` 함수는 유지 (분석/전략 페이지에서 사용 예정)

### 2. 이번 달 성적표 (목표 대비) 섹션
**위치**: `_render_analysis_section()` 호출 (1526-1539줄)
**제거 내용**:
- expander "📊 이번 달 성적표 (목표 대비)"
- 목표 매출 달성률
- 총비용률 비교
- 영업이익 비교
- 이익률 비교
- 카테고리별 비교 테이블
- 문제 원인 TOP 3
- 한 줄 코멘트

**함수 유지**: `_render_analysis_section()` 함수는 유지 (분석/전략 페이지에서 사용 예정)

### 3. 월별 성적 히스토리 섹션
**위치**: `_render_settlement_history()` 호출 (1541-1554줄)
**제거 내용**:
- expander "📊 월별 성적 히스토리"
- 월별 성적 히스토리 테이블
- 월별 상세 보기 버튼들
- 더 보기/줄이기 버튼

**함수 유지**: `_render_settlement_history()` 함수는 유지 (분석/전략 페이지에서 사용 예정)

### 4. PDF 성적표 다운로드 버튼
**위치**: Action Bar Secondary 액션 (1598-1633줄)
**제거 내용**:
- PDF 다운로드 버튼 및 로직
- PDF 생성 관련 import 및 함수 호출

**참고**: PDF 기능은 분석/전략 페이지로 이동 예정

### 5. 분석/전략 관련 Import
**위치**: 33-35줄
**제거 내용**:
- `from ui_pages.monthly_structure_report import build_monthly_structure_report`
- `from ui_pages.coach.coach_renderer import render_verdict_card`
- `from ui_pages.routines.routine_state import get_routine_status, mark_monthly_review_done`

**처리**: 주석 처리 (함수는 유지하므로 import는 나중에 분석 페이지에서 사용)

## 현재 페이지에 남은 섹션 구조

### 1. 상단 블록: 정산 기간 선택
**위치**: `_render_header_section()` 내부 (248-285줄)
**내용**:
- 연도 선택 (number_input)
- 월 선택 (number_input)
- `ps_section("정산 기간 선택", icon="📅")` 사용

### 2. 이번 달 성적표 블록: KPI 요약
**위치**: `_render_header_section()` 내부 (285-406줄)
**내용**:
- `ps_section("이번 달 성적표", icon="📊")` 사용
- 총매출 입력 (FormKit `ps_money_input`)
  - 매출 불러오기 버튼 → Action Bar Secondary로 이동
  - 자동값으로 버튼 → Action Bar Secondary로 이동
- 미마감 경고 (필수 안내)
- KPI 카드 4개:
  - 총매출 (st.metric)
  - 총비용 (st.metric)
  - 영업이익 (st.metric)
  - 이익률 (st.metric)
- 상태 배지 (확정됨/작성중)

### 3. 비용 입력 블록
**위치**: `_render_expense_section()` (868줄)
**내용**:
- `ps_section("비용 입력", icon="💸")` 사용
- 5개 카테고리별 입력:
  - 임차료 (고정비)
  - 인건비 (고정비)
  - 재료비 (매출연동)
  - 공과금 (고정비)
  - 부가세&카드수수료 (매출연동)
- 각 항목별:
  - 항목명 입력
  - 입력방식 선택 (금액/비율)
  - 금액 또는 비율 입력 (FormKit 사용)
  - 템플릿 저장/삭제 버튼 (항목별 작업용, 유지)
  - 새 항목 추가

### 4. 하단 Action Bar
**위치**: `render_form_layout()` 호출 (1634-1647줄)
**내용**:
- Primary: 이번달 저장(draft) 또는 확정 해제 (상태에 따라)
- Secondary:
  - 🔄 템플릿 다시 불러오기
  - 🔄 매출 불러오기
  - ↩️ 자동값으로
  - 📥 저장값 불러오기
  - ✅ 이번달 확정 (draft 상태일 때만)

## 페이지 구조 요약

```
월간 정산 입력 페이지 (입력 전용)
├── Header (제목 + 상태배지)
├── GuideBox (G3)
├── Summary Strip (정산 기간, 총매출)
├── Action Bar (상단 고정)
├── Main Card
│   ├── 1. 정산 기간 선택 (연/월)
│   ├── 2. 이번 달 성적표 (KPI 요약)
│   │   ├── 총매출 입력
│   │   ├── 미마감 경고
│   │   └── KPI 카드 4개
│   └── 3. 비용 입력
│       ├── 임차료
│       ├── 인건비
│       ├── 재료비
│       ├── 공과금
│       └── 부가세&카드수수료
└── Action Bar (하단)
```

## 제거된 함수 호출 (함수 자체는 유지)

1. `_render_structure_report_section(store_id, year, month)` - 호출 제거, 함수 유지
2. `_render_analysis_section(store_id, year, month, expense_items, totals, total_sales)` - 호출 제거, 함수 유지
3. `_render_settlement_history(store_id)` - 호출 제거, 함수 유지
4. `handle_pdf_download()` - 함수 제거 (Action Bar에서)

## 변경 파일

**수정**: `ui_pages/settlement_actual.py`
- 구조 판결 섹션 호출 제거 (1521줄)
- 분석 섹션 expander 제거 (1526-1539줄)
- 히스토리 섹션 expander 제거 (1541-1554줄)
- PDF 다운로드 버튼 제거 (1598-1633줄)
- 분석/전략 관련 import 주석 처리 (33-35줄)

## 결론

**P3 작업 완료**: ✅ 입력 전용 페이지로 역할 분리 완료

- 제거된 섹션: 4개 (구조 판결, 성적표 분석, 히스토리, PDF)
- 남은 섹션: 3개 (기간 선택, 성적표 KPI, 비용 입력)
- 페이지 구조: 입력 흐름이 위 → 아래로 자연스럽게 이어짐
- 해석/판단/전략 요소: 0개

페이지가 "작성 화면"처럼 보이도록 정리되었습니다. 제거된 섹션들은 이후 분석/전략 페이지에서 재사용할 수 있도록 함수는 모두 유지했습니다.
