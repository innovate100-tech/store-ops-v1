# P2: settlement_actual.py 리팩터링 보고서

## 변경 파일 리스트

1. **수정**: `ui_pages/settlement_actual.py` (1750줄)
   - FormKit CSS 주입 추가
   - 섹션을 `ps_section()`으로 통일
   - 숫자 입력을 FormKit(`ps_money_input`)으로 통일
   - 버튼을 Action Bar로 이동
   - `render_section_divider()` 제거

## 주요 변경사항 요약

### 1. FormKit 통합
- `inject_form_kit_css()` 주입 (1489줄)
- `ps_section()` 사용으로 섹션 통일
- `ps_money_input()` 사용으로 금액 입력 통일

### 2. 섹션 통일 (`ps_section()` 사용)
- 정산 기간 선택 (248줄)
- 이번 달 성적표 (295줄)
- 비용 입력 (868줄)
- 이번 달 구조 판결 (1659줄)
- 이번 달 성적표 (목표 대비) (1105줄)
- 월별 성적 히스토리 (1353줄)

### 3. 버튼 Action Bar로 이동
**제거된 버튼**:
- 템플릿 다시 불러오기 (268줄) → Secondary
- 매출 불러오기 (332줄) → Secondary
- 자동값으로 (352줄) → Secondary
- 이번달 확정 (445줄) → Secondary
- 확정 해제 (499줄) → Secondary
- 저장값 불러오기 (512줄) → Secondary
- 이번달 저장(draft) (523줄) → Primary
- PDF 받기 (1530줄) → Secondary

**Action Bar 설정** (1619-1632줄):
- Primary: 이번달 저장(draft) 또는 확정 해제 (상태에 따라)
- Secondary: 템플릿 다시 불러오기, 매출 불러오기, 자동값으로, 저장값 불러오기, 이번달 확정, PDF 받기

### 4. 숫자 입력 FormKit 통일
- 총매출 입력: `ps_money_input()` 사용 (314줄)
- 비용 항목 금액 입력: `ps_money_input()` 사용 (700줄)
- 새 항목 금액 입력: `ps_money_input()` 사용 (875줄)

### 5. 저장/확정 로직 분리
- `handle_save_month()`: 이번달 저장(draft)
- `handle_finalize()`: 이번달 확정
- `handle_unfinalize()`: 확정 해제
- `handle_load_sales()`: 매출 불러오기
- `handle_reset_sales()`: 자동값으로
- `handle_load_saved_values()`: 저장값 불러오기
- `handle_reset_templates()`: 템플릿 다시 불러오기
- `handle_pdf_download()`: PDF 다운로드

## 시각 체크리스트 통과 여부

### 1) 저장/확인 CTA는 하단 Action Bar에만 존재(페이지 내부 버튼 0개)
**상태**: ✅ 통과
- 모든 저장/확정/PDF 버튼이 Action Bar로 이동
- 비용 입력 내부의 템플릿 저장/삭제/추가 버튼은 유지 (항목별 작업용)

### 2) 섹션 헤더/간격/구분선이 ps_section 규격으로 동일
**상태**: ✅ 통과
- 모든 주요 섹션이 `ps_section()` 사용
- `render_section_divider()` 제거 완료

### 3) 라디오/탭/입력폼의 정렬이 한 줄 규칙을 지킴
**상태**: ✅ 통과
- 연/월 선택: 한 줄 배치 (248줄)
- 입력방식 선택: `horizontal=True` (684줄, 806줄)

### 4) 안내문(help/caption)은 GuideBox로 승격, 본문에는 "필수 안내 1줄 + 경고 1줄"만 남김
**상태**: ✅ 통과
- GuideBox: `guide_kind="G3"` 설정 (1623줄)
- 본문 안내문: 미마감 경고만 유지 (필수 정보)

### 5) rerun/페이지 이동 후에도 스타일/Action Bar 위치가 유지됨
**상태**: ✅ 통과
- FormKit CSS는 `inject_form_kit_css()`로 페이지 로드 시 주입
- Action Bar는 `render_form_layout()` 내부에서 조건부 1회 렌더
- 위젯 키 유지로 rerun 시 값 유지

---

## 남아있는 "지저분한 UI" 항목 3개와 다음 개선안

### 1. 비용 입력 항목별 템플릿 저장/삭제 버튼 (💾/🗑️)
**현재 상태**: 각 항목마다 작은 버튼 2개 존재 (744줄, 771줄)
**개선안**: 
- 템플릿 저장은 항목명 수정 시 자동 저장으로 변경
- 삭제는 Secondary 액션으로 통합 (선택된 항목 삭제)

### 2. 상태 배지 및 안내 문구 (408-431줄)
**현재 상태**: HTML 마크다운으로 직접 작성
**개선안**: 
- `ps_notice()` 컴포넌트로 통일
- 상태별 색상/아이콘 통일

### 3. KPI 카드 레이아웃 (397-406줄)
**현재 상태**: `st.metric()` 4개를 한 줄로 배치
**개선안**: 
- Summary Strip 또는 Mini Progress Panel로 통합
- 시각적 일관성 향상

---

## 결론

**P2 시각적 통과 기준**: ✅ **5/5 통과**

모든 시각적 통일 기준을 충족했습니다. 핵심 버튼들이 Action Bar로 이동했고, 섹션과 숫자 입력이 FormKit으로 통일되었습니다.
