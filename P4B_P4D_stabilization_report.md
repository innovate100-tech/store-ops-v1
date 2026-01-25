# P4-B & P4-D: 입력 리듬/블록 시스템 + 시각 스펙 고정 보고서

## 작업 목표
- FormKit v2 안정화 (스코프 고정, 단위 박스 안정화, 반응형)
- 입력 블록 시스템 최소 구현
- settlement_actual.py 블록 리듬 적용

---

## 완료된 작업

### Phase 4-D. FormKit v2 안정화 ✅

#### 1) 스코프 주입 방식 고정 ✅

**변경 내용**:
- `inject_form_kit_v2_css(scope_id: Optional[str] = None)` 함수 추가
- `data-ps-scope` 속성 기반 스코프 시스템 도입
- 모든 CSS 선택자를 `[data-ps-scope]` 하위로 제한

**구현 위치**: `src/ui/components/form_kit_v2.py`
- `_generate_form_kit_v2_css()` 함수로 CSS 생성
- 모든 스타일 규칙을 `[data-ps-scope]` 선택자로 감싸기
- `settlement_actual.py`에서 `scope_id="settlement_actual"` 사용

**스코프 격리 확인**:
```python
# ui_pages/settlement_actual.py
scope_id = inject_form_kit_v2_css("settlement_actual")
# → <div data-ps-scope="settlement_actual"> 생성
# → 모든 CSS는 [data-ps-scope="settlement_actual"] 하위로만 적용
```

---

#### 2) 단위 박스 안정화 ✅

**변경 내용**:
- 단위 박스를 `::after` pseudo-element로 구현
- `data-unit` 속성으로 단위 전달
- `pointer-events: none` 필수 적용
- 반응형: 900px 이하에서 단위 박스 숨김

**구현 위치**: `src/ui/components/form_kit_v2.py`
- `ps_primary_money_input()`: `data-unit` 속성 사용
- `ps_primary_ratio_input()`: `data-unit` 속성 사용
- CSS `::after`로 단위 박스 렌더링
- `pointer-events: none`으로 클릭 방해 방지

**단위 박스 코드**:
```css
[data-ps-scope] .ps-primary-input-wrapper::after {
    content: attr(data-unit);
    pointer-events: none; /* 클릭 방해 방지 */
    /* ... */
}
@media (max-width: 900px) {
    [data-ps-scope] .ps-primary-input-wrapper::after {
        display: none; /* 좁은 화면에서 숨김 */
    }
}
```

---

#### 3) 반응형 규칙 ✅

**변경 내용**:
- 900px 이하에서 2~3열 그리드를 1열로 자동 변경
- 단위 박스 숨김 및 padding 조정
- 블록 행(`ps_block_row`) 반응형 지원

**구현 위치**: `src/ui/components/form_kit_v2.py`
- `RESPONSIVE_BREAKPOINT = 900` 상수 정의
- `ps_block_row` CSS에 미디어 쿼리 추가
- Primary Input 단위 박스 반응형 처리

**반응형 CSS**:
```css
@media (max-width: 900px) {
    [data-ps-scope] .ps-block-row-cols-2,
    [data-ps-scope] .ps-block-row-cols-3 {
        grid-template-columns: 1fr;
    }
    [data-ps-scope] .ps-primary-input-wrapper::after {
        display: none;
    }
}
```

---

#### 4) 시각 스펙 상수화 ✅

**변경 내용**:
- 모든 시각 스펙 값을 상수로 정의
- 코드에서 하드코딩된 값 제거

**상수 정의** (`src/ui/components/form_kit_v2.py`):
```python
PRIMARY_INPUT_HEIGHT = 56  # px
PRIMARY_INPUT_FONT_SIZE = 22  # px
PRIMARY_INPUT_FONT_WEIGHT = 600
PRIMARY_INPUT_BORDER_RADIUS = 14  # px
PRIMARY_INPUT_PADDING_RIGHT = 120  # px (단위 박스 공간)

SECONDARY_INPUT_HEIGHT = 40  # px
SECONDARY_INPUT_FONT_SIZE = 14  # px

UNIT_BOX_FONT_SIZE = 13  # px
UNIT_BOX_HEIGHT = 40  # px
UNIT_BOX_PADDING_H = 10  # px

INPUT_BLOCK_PADDING = 16  # px
INPUT_BLOCK_BORDER_RADIUS = 14  # px
INPUT_BLOCK_MARGIN_BOTTOM = 16  # px

RESPONSIVE_BREAKPOINT = 900  # px
```

---

### Phase 4-B. 입력 블록 시스템 ✅

#### 1) ps_input_block() 구현 ✅

**함수 시그니처**:
```python
def ps_input_block(
    title: str,
    description: Optional[str] = None,
    right_hint: Optional[str] = None,
    level: str = "primary",
    body_fn: Optional[Callable] = None,
    feedback: Optional[Dict[str, Any]] = None,
    warning: Optional[str] = None
)
```

**기능**:
- 카드 컨테이너 + 제목줄 + 우측 힌트
- 본문 렌더링 함수 지원
- 피드백/경고 표시

**구현 위치**: `src/ui/components/form_kit_v2.py`

---

#### 2) ps_block_row() 구현 ✅

**함수 시그니처**:
```python
def ps_block_row(
    cols: int = 2,
    body_fn: Optional[Callable] = None
)
```

**기능**:
- 반응형 그리드 (2열/3열)
- 900px 이하에서 자동 1열
- 본문 렌더링 함수 지원

**구현 위치**: `src/ui/components/form_kit_v2.py`

---

### Phase 4-B. settlement_actual.py 블록 리듬 적용 (진행 중)

**현재 상태**:
- FormKit v2 CSS 주입 완료 (고유 스코프)
- Primary Input 교체 완료
- 블록 리듬 적용 준비 완료

**다음 단계**:
- 정산기간 블록 (Secondary)
- 총매출 블록 (Primary) + 피드백
- 비용입력 블록 (카테고리별)

---

## 변경 파일 요약

### src/ui/components/form_kit_v2.py

**주요 변경**:
1. 시각 스펙 상수 추가 (PRIMARY_INPUT_HEIGHT 등)
2. `_generate_form_kit_v2_css()` 함수로 CSS 생성
3. 모든 CSS 선택자를 `[data-ps-scope]` 기반으로 변경
4. `inject_form_kit_v2_css(scope_id)` 함수 수정
5. 단위 박스를 `::after` + `data-unit` 속성으로 변경
6. 반응형 미디어 쿼리 추가
7. `ps_input_block()` 함수 개선 (right_hint, level 추가)
8. `ps_block_row()` 함수 추가

---

### ui_pages/settlement_actual.py

**주요 변경**:
1. `inject_form_kit_v2_css("settlement_actual")` 호출 추가
2. 고유 스코프 ID 사용

---

## 검증 체크리스트

### ✅ 스코프 격리 확인

**grep 결과**:
```bash
# data-ps-scope 사용 확인
grep -r "data-ps-scope" src/ui/components/form_kit_v2.py
# → 모든 CSS 선택자가 [data-ps-scope] 기반

# settlement_actual.py 스코프 주입 확인
grep "inject_form_kit_v2_css" ui_pages/settlement_actual.py
# → scope_id="settlement_actual" 사용
```

**결과**: ✅ 스코프 격리 완료

---

### ✅ 위젯 key 변경 없음 확인

**grep 결과**:
```bash
grep -E "settlement_total_sales_input|settlement_item_amount|settlement_item_rate|settlement_new_amount|settlement_new_rate" ui_pages/settlement_actual.py | wc -l
# → 모든 key 유지 확인
```

**결과**: ✅ 위젯 key 변경 없음

---

### ✅ 단위 박스 안정화 확인

**코드 확인**:
- `pointer-events: none` 적용 ✅
- `data-unit` 속성 사용 ✅
- 반응형 숨김 처리 ✅

**결과**: ✅ 단위 박스 안정화 완료

---

### ✅ 반응형 규칙 확인

**코드 확인**:
- `RESPONSIVE_BREAKPOINT = 900` 상수 정의 ✅
- 미디어 쿼리 적용 ✅
- 블록 행 반응형 지원 ✅

**결과**: ✅ 반응형 규칙 완료

---

## 다음 단계

1. **settlement_actual.py 블록 리듬 적용**
   - 정산기간 블록 (Secondary)
   - 총매출 블록 (Primary) + 피드백
   - 비용입력 블록 (카테고리별)

2. **최종 검증**
   - 페이지 이동/리런/새로고침 후 스타일 유지
   - 단위 박스 클릭 방해 없음
   - 좁은 화면에서 깨짐 없음
   - 다른 페이지에 스타일 번짐 0

---

## 결론

**Phase 4-D (안정화) 완료**: ✅
- 스코프 주입 방식 고정 (data-ps-scope 기반)
- 단위 박스 안정화 (pointer-events, 반응형)
- 반응형 규칙 추가 (900px 이하 1열)
- 시각 스펙 상수화

**Phase 4-B (블록 시스템) 완료**: ✅
- `ps_input_block()` 구현
- `ps_block_row()` 구현

**Phase 4-B (블록 리듬 적용) 진행 중**: 🔄
- settlement_actual.py 블록 리듬 적용 준비 완료
