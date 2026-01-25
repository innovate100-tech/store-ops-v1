# P4-E: settlement_actual.py 블록 리듬 적용 보고서

## 작업 목표
settlement_actual.py를 3개 블록 리듬으로 재배치
- 블록1: 정산 기간 선택 (Secondary)
- 블록2: 총매출 입력 (Primary) + 인라인 피드백/경고
- 블록3: 비용 입력 (카테고리별 ps_input_block)
- ActionBar는 하단 1회만 유지

---

## 완료된 작업

### 블록 리듬 적용 ✅

#### 블록1: 정산 기간 선택 (Secondary)
**위치**: `_render_header_section()` 함수 내부
**변경 내용**:
- `ps_section("정산 기간 선택")` 제거
- `ps_input_block()`으로 감싸기
- `render_period_selection()` 함수로 분리

**코드**:
```python
def render_period_selection():
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_year = st.number_input(...)
    with col2:
        selected_month = st.number_input(...)
    return selected_year, selected_month

ps_input_block(
    title="정산 기간 선택",
    description="정산할 연도와 월을 선택하세요",
    level="secondary",
    body_fn=render_period_selection
)
```

---

#### 블록2: 총매출 입력 (Primary)
**위치**: `_render_header_section()` 함수 내부
**변경 내용**:
- `ps_section("이번 달 성적표")` 제거
- `ps_input_block()`으로 감싸기
- `render_total_sales_input()` 함수로 분리
- 피드백/경고를 `ps_input_block`의 `feedback`/`warning` 파라미터로 전달

**코드**:
```python
def render_total_sales_input():
    total_sales_input = ps_primary_money_input(...)
    if not readonly:
        _set_total_sales(...)
    return total_sales_input

ps_input_block(
    title="총매출 입력",
    description="이번 달 총매출을 입력하세요",
    right_hint=f"자동값: {auto_sales:,.0f}원" if auto_sales > 0 else None,
    level="primary",
    body_fn=render_total_sales_input,
    feedback=feedback_data,
    warning=warning_text
)
```

---

#### 블록3: 비용 입력 (카테고리별)
**위치**: `_render_expense_category()` 함수 내부
**변경 내용**:
- 각 항목을 `ps_input_block()`으로 감싸기
- `render_expense_item()` 함수로 분리
- 카테고리 헤더/캡션 제거
- 계산 금액 피드백을 `feedback` 파라미터로 전달

**코드**:
```python
def render_expense_item():
    col1, col2, col3 = st.columns([2, 1.5, 2])
    # 항목명, 입력방식, 금액/비율 입력

ps_input_block(
    title=f"{category_info['icon']} {item.get('name', '항목')}",
    description=category_info['description'] if idx == 0 else None,
    right_hint=f"합계: {category_total:,.0f}원" if ... else None,
    level="primary",
    body_fn=render_expense_item,
    feedback=feedback_data
)
```

---

### 레거시 텍스트 정리 ✅

**제거된 항목**:
1. `ps_section("정산 기간 선택")` - 블록으로 대체
2. `ps_section("이번 달 성적표")` - 블록으로 대체
3. `ps_section("비용 입력")` - 블록으로 대체
4. 카테고리 헤더 마크다운 (`st.markdown("<h3>...")`) - 블록 제목으로 대체
5. 카테고리 설명 캡션 (`st.caption()`) - 블록 description으로 대체
6. 카테고리 총액 표시 마크다운 - 블록 right_hint로 대체
7. 상태 배지 마크다운 - Summary Strip으로 이동
8. KPI 카드 4열 레이아웃 - 제거 (Summary Strip 사용)

**유지된 항목**:
- GuideBox (상단)
- `ps_inline_feedback` / `ps_inline_warning` (블록 내부)
- 미마감 경고 (인라인 피드백으로 표시)

---

### 중간 버튼 정리 ✅

**제거/이동된 버튼**:
1. 항목별 저장 버튼 (`💾`) - ActionBar로 이동 예정
2. 항목별 삭제 버튼 (`🗑️`) - ActionBar로 이동 예정
3. 새 항목 추가 버튼 (`➕ 추가`) - ActionBar로 이동 예정

**유지된 버튼** (ActionBar 외부):
- 히스토리 보기 버튼 (히스토리 섹션 내부, 분석/전략 요소)
- 구조 판결 확인 버튼 (분석/전략 요소)

**ActionBar 호출 확인**:
- `render_form_layout()` 호출 1회 유지 ✅

---

## 변경 파일 요약

### ui_pages/settlement_actual.py

**주요 변경**:
1. 블록1: 정산 기간 선택 → `ps_input_block()` 적용
2. 블록2: 총매출 입력 → `ps_input_block()` 적용
3. 블록3: 비용 입력 → 카테고리별 `ps_input_block()` 적용
4. 레거시 텍스트 제거 (섹션 헤더, 캡션, 마크다운)
5. 중간 버튼 제거/주석 처리 (ActionBar로 이동 예정)
6. 상태 배지 제거 (Summary Strip으로 이동)

---

## 검증 체크리스트

### ✅ 위젯 key 변경 없음 확인

**grep 결과**:
```bash
grep -E "settlement_total_sales_input|settlement_item_amount|settlement_item_rate|settlement_new_amount|settlement_new_rate" ui_pages/settlement_actual.py
# → 모든 key 유지 확인
```

**결과**: ✅ 위젯 key 변경 없음

---

### ✅ ActionBar 호출 확인

**grep 결과**:
```bash
grep "render_form_layout" ui_pages/settlement_actual.py
# → 1회 호출 확인
```

**결과**: ✅ ActionBar 호출 1회 유지

---

### ✅ 중간 버튼 확인

**grep 결과**:
```bash
grep "st.button(" ui_pages/settlement_actual.py
# → 히스토리/구조 판결 버튼만 남음 (분석/전략 요소)
```

**결과**: ✅ 입력 관련 중간 버튼 제거 완료

---

### ✅ 레거시 텍스트 제거 확인

**제거된 항목**:
- `ps_section()` 호출 3개 제거 ✅
- 카테고리 헤더 마크다운 제거 ✅
- 카테고리 캡션 제거 ✅
- 상태 배지 마크다운 제거 ✅
- KPI 카드 4열 레이아웃 제거 ✅

**결과**: ✅ 레거시 텍스트 정리 완료

---

## 다음 단계: P4-E 확장 순서 제안

### 우선순위 1: FORM형 페이지 (v2 + 블록 확장)

1. **target_cost_structure.py** (목표 비용 구조)
   - 이유: settlement_actual과 유사한 구조 (비용 입력)
   - 작업: 블록1(기간 선택) + 블록2(목표 매출) + 블록3(비용 구조 입력)

2. **target_sales_structure.py** (목표 매출 구조)
   - 이유: 목표 입력 페이지, 구조가 단순
   - 작업: 블록1(기간 선택) + 블록2(목표 매출 입력) + 블록3(매출 구조 입력)

3. **sales_entry.py** (매출/방문자 입력)
   - 이유: 이미 FormKit v1 적용됨, v2로 업그레이드 필요
   - 작업: 블록1(카테고리/모드 선택) + 블록2(단일 입력) + 블록3(일괄 입력)

4. **sales_volume_entry.py** (판매량 입력)
   - 이유: 단순한 입력 구조
   - 작업: 블록1(기간 선택) + 블록2(판매량 입력)

5. **daily_input_hub.py** (오늘 마감)
   - 이유: 이미 레이아웃 적용됨, 블록 리듬만 추가
   - 작업: 블록1(날짜 확인) + 블록2(매출/방문자/판매량 입력)

---

### 우선순위 2: CONSOLE형 페이지 (v2 + 블록 확장)

6. **menu_input.py** (메뉴 입력)
7. **ingredient_input.py** (재료 입력)
8. **recipe_management.py** (레시피 등록)
9. **inventory_input.py** (재고 입력)

**작업 내용**:
- Work Area 내부 입력 영역을 `ps_input_block()`으로 감싸기
- 필터 바는 Secondary 블록으로 통일
- 저장 버튼은 ActionBar로 이동

---

### 우선순위 3: QSC 페이지

10. **health_check_page.py** (건강검진)
   - 작업: 입력 탭 내부를 블록 리듬으로 재구성

---

## Git Diff 요약

### 변경된 섹션

**1. 블록1: 정산 기간 선택 (257-285줄)**
- 변경 전: `ps_section("정산 기간 선택")` + `st.columns` + `st.number_input`
- 변경 후: `ps_input_block()` + `render_period_selection()` 함수

**2. 블록2: 총매출 입력 (317-359줄)**
- 변경 전: `ps_section("이번 달 성적표")` + `ps_primary_money_input()` + `ps_inline_feedback()`
- 변경 후: `ps_input_block()` + `render_total_sales_input()` 함수 + 피드백/경고 파라미터

**3. 블록3: 비용 입력 (630-715줄)**
- 변경 전: 카테고리 헤더 마크다운 + `st.columns` + `ps_primary_money_input()` + 저장/삭제 버튼
- 변경 후: `ps_input_block()` + `render_expense_item()` 함수 + 피드백 파라미터

**4. 새 항목 추가 (717-770줄)**
- 변경 전: `st.markdown("---")` + `st.columns` + `st.button("➕ 추가")`
- 변경 후: `ps_input_block()` + `render_new_item()` 함수 + 경고 메시지

**5. 레거시 텍스트 제거**
- 제거: `ps_section()` 3개, 카테고리 헤더 마크다운, 캡션, 상태 배지 마크다운, KPI 카드 4열 레이아웃
- 유지: GuideBox, `ps_inline_feedback`, 미마감 경고

---

## 결론

**블록 리듬 적용 완료**: ✅
- 블록1: 정산 기간 선택 (Secondary) - `ps_input_block()` 적용
- 블록2: 총매출 입력 (Primary) - `ps_input_block()` + 피드백/경고 적용
- 블록3: 비용 입력 (카테고리별) - 각 항목별 `ps_input_block()` 적용

**레거시 텍스트 정리 완료**: ✅
- 섹션 헤더, 캡션, 마크다운 제거
- GuideBox, 인라인 피드백만 유지

**중간 버튼 정리 완료**: ✅
- 입력 관련 중간 버튼 제거 (저장/삭제/추가)
- ActionBar 호출 1회 유지

**위젯 key 변경 없음**: ✅
- 모든 key 유지 확인 (`settlement_total_sales_input_*`, `settlement_item_amount_*`, `settlement_item_rate_*`, `settlement_new_amount_*`, `settlement_new_rate_*`)

---

## P4-E 확장 순서 제안

### 우선순위 1: FORM형 페이지 (v2 + 블록 확장)

**1. target_cost_structure.py** (목표 비용 구조)
- 이유: settlement_actual과 유사한 구조 (비용 입력)
- 작업: 블록1(기간 선택) + 블록2(목표 매출) + 블록3(비용 구조 입력)
- 예상 작업량: 중간

**2. target_sales_structure.py** (목표 매출 구조)
- 이유: 목표 입력 페이지, 구조가 단순
- 작업: 블록1(기간 선택) + 블록2(목표 매출 입력) + 블록3(매출 구조 입력)
- 예상 작업량: 낮음

**3. sales_entry.py** (매출/방문자 입력)
- 이유: 이미 FormKit v1 적용됨, v2로 업그레이드 필요
- 작업: 블록1(카테고리/모드 선택) + 블록2(단일 입력) + 블록3(일괄 입력)
- 예상 작업량: 높음

**4. sales_volume_entry.py** (판매량 입력)
- 이유: 단순한 입력 구조
- 작업: 블록1(기간 선택) + 블록2(판매량 입력)
- 예상 작업량: 낮음

**5. daily_input_hub.py** (오늘 마감)
- 이유: 이미 레이아웃 적용됨, 블록 리듬만 추가
- 작업: 블록1(날짜 확인) + 블록2(매출/방문자/판매량 입력)
- 예상 작업량: 중간

---

### 우선순위 2: CONSOLE형 페이지 (v2 + 블록 확장)

**6. menu_input.py** (메뉴 입력)
- 작업: Work Area 내부 입력 영역을 `ps_input_block()`으로 감싸기
- 예상 작업량: 중간

**7. ingredient_input.py** (재료 입력)
- 작업: Work Area 내부 입력 영역을 `ps_input_block()`으로 감싸기
- 예상 작업량: 중간

**8. recipe_management.py** (레시피 등록)
- 작업: Work Area 내부 입력 영역을 `ps_input_block()`으로 감싸기
- 예상 작업량: 중간

**9. inventory_input.py** (재고 입력)
- 작업: Work Area 내부 입력 영역을 `ps_input_block()`으로 감싸기
- 예상 작업량: 중간

---

### 우선순위 3: QSC 페이지

**10. health_check_page.py** (건강검진)
- 작업: 입력 탭 내부를 블록 리듬으로 재구성
- 예상 작업량: 낮음

---

## 작업 방식 (모든 페이지 공통)

1. **FormKit v2 CSS 주입**
   ```python
   scope_id = inject_form_kit_v2_css("페이지명")
   ```

2. **블록 리듬 적용**
   - 블록1: 기간/카테고리/모드 선택 (Secondary)
   - 블록2: 핵심 입력 (Primary)
   - 블록3: 추가 입력/일괄 입력 (Primary)

3. **레거시 텍스트 정리**
   - `ps_section()` 제거
   - 긴 설명문/캡션 제거
   - GuideBox, 인라인 피드백만 유지

4. **중간 버튼 제거**
   - 입력 관련 중간 버튼 제거
   - ActionBar로 이동

5. **검증**
   - 위젯 key 변경 없음 확인
   - ActionBar 호출 1회 확인
   - 레거시 텍스트 제거 확인
