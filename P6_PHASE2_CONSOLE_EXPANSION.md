# P6 Phase 2 CONSOLE형 확장 보고서

## 1. 변경 파일 목록

| 파일 | 변경 요약 |
|------|-----------|
| `ui_pages/input/menu_input.py` | `inject_form_kit_v2_css("menu_input")` 추가, `ps_section` import, Zone E에 `menu_has_recipe` 전달, `ps_secondary_select` index 호환 |
| `ui_pages/input/ingredient_input.py` | `ps_section` import 추가 (FormKit v2·블록 리듬은 기 적용) |
| `ui_pages/recipe_management.py` | `ps_section`·`ui_flash_*` import, Work Area `ps_input_block` 래핑, 사용량→`ps_primary_quantity_input`·재료비→`ps_inline_feedback`, 조리방법→`ps_note_input`, 내부 "💾 일괄 저장" 제거 후 ActionBar CTA로 이동 |
| `ui_pages/input/inventory_input.py` | `inject_form_kit_v2_css("inventory_input")`, `ps_input_block`·`ps_inline_feedback`·`ps_input_status_badge` 추가, Dashboard 버튼 제거, Zone C 저장/초기화 버튼 제거, `_render_inventory_action_bar` 추가(저장·불러오기·초기화 하단 1곳), `render_section_header`→`ps_section`, 행 상태→`ps_input_status_badge` |

---

## 2. 적용 scope_id

| 페이지 | scope_id |
|--------|----------|
| menu_input | `menu_input` |
| ingredient_input | `ingredient_input` |
| recipe_management | `recipe_management` |
| inventory_input | `inventory_input` |

- 모든 CSS는 `inject_form_kit_v2_css(scope_id)`로 스코프 격리.

---

## 3. key= 변경 없음 (grep 근거)

- `menu_input.py`: `key=` **32건** (기존 key 유지).
- `ingredient_input.py`: `key=` **39건** (기존 key 유지).
- `recipe_management.py`: `key=` **11건** (기존 key 유지).
- `inventory_input.py`: `key=` **12건** (액션 버튼 `inventory_act_*` 추가, 기존 `inventory_*` key 변경 없음).

---

## 4. ActionBar 1회 렌더 근거

### menu_input

- `render_console_layout(..., cta_label=..., cta_action=...)` 호출 **1회** (라인 ~111).
- CTA는 `action_primary`(단일/일괄 저장)에서만 설정. 레이아웃 하단 CTA 1곳.

### ingredient_input

- `render_console_layout(..., cta_label=..., cta_action=...)` 호출 **1회** (라인 ~139).
- CTA는 `action_primary`(단일/일괄 저장)에서만 설정. 레이아웃 하단 CTA 1곳.

### recipe_management

- `render_console_layout(..., cta_label=..., cta_action=...)` 호출 **1회** (라인 ~642).
- CTA는 `action_primary`("💾 일괄 저장")에서만 설정. Work Area 내부 "💾 일괄 저장" 제거, 하단 CTA 1곳.

### inventory_input

- `render_console_layout`의 CTA는 사용하지 않음 (`cta_label=None`, `cta_action=None`).
- 저장·불러오기·초기화는 **`_render_inventory_action_bar`** 단일 블록(`ps_input_block`)에서만 렌더 (하단 1곳).  
  Dashboard·Zone C의 저장/초기화/불러오기 버튼 제거.

---

## 5. 페이지별 Before / After 요약

### menu_input

| 구분 | Before | After |
|------|--------|-------|
| FormKit v2 | inject만, scope 미사용 | `inject_form_kit_v2_css("menu_input")` 적용 |
| 섹션 | `ps_section` 사용, import 누락 | `ps_section` import 추가 |
| Zone E | `menu_has_recipe` 미전달 | `menu_has_recipe` 인자로 전달 |
| 저장 | ActionBar(단일/일괄) 1곳 | 동일 유지 |

### ingredient_input

| 구분 | Before | After |
|------|--------|-------|
| FormKit v2 | 적용됨 | 동일 |
| 섹션 | `ps_section` 사용, import 누락 | `ps_section` import 추가 |
| 저장 | ActionBar(단일/일괄) 1곳 | 동일 유지 |

### recipe_management

| 구분 | Before | After |
|------|--------|-------|
| Work Area | `_body_recipe` 정의만, 미호출 | `ps_input_block`으로 래핑, `body_fn=_body_recipe` 호출 |
| 사용량 | `st.number_input` | `ps_primary_quantity_input` (단위 반영) |
| 재료비 | `st.markdown` | `ps_inline_feedback` |
| 조리방법 | `st.text_area` | `ps_note_input` |
| 저장 | Work Area 내 "💾 일괄 저장" | 제거, ActionBar "💾 일괄 저장" 1곳 |

### inventory_input

| 구분 | Before | After |
|------|--------|-------|
| FormKit v2 | 미사용 | `inject_form_kit_v2_css("inventory_input")` + `ps_input_block`·`ps_inline_feedback`·`ps_input_status_badge` |
| Dashboard | `render_section_header` + 불러오기/초기화/전체 저장 버튼 | `ps_section` + KPI만 (버튼 제거) |
| Zone C | 변경된 항목 표시 + 저장/초기화 버튼 | 변경된 항목 표시 + `ps_inline_feedback`만, 버튼 제거 |
| 저장/불러오기/초기화 | Dashboard·Zone C에 분산 | `_render_inventory_action_bar` 하단 1곳 (변경 저장·전체 저장·불러오기·초기화) |
| 행 상태 | `st.markdown`+색상 | `ps_input_status_badge` |

---

## 6. 중간 저장 버튼 0개 (grep 요약)

- **menu_input**: Work Area 저장 없음. "💾 저장"은 List 수정 모달(행 단위)에만 존재 → 행 단위 액션 유지.
- **ingredient_input**: Work Area 저장 없음. "💾 저장"은 List 수정 모달(행 단위)에만 존재 → 행 단위 액션 유지.
- **recipe_management**: Work Area 내 "💾 일괄 저장" **제거** → ActionBar CTA 1곳만.
- **inventory_input**: Dashboard·Zone C의 저장/초기화/불러오기 **제거** → `_render_inventory_action_bar` 하단 1곳만.

**결과**: CONSOLE형 4페이지 모두 **중간 저장 버튼 0개**. 저장·불러오기·초기화는 하단 ActionBar/액션 블록 1곳에만 존재.

---

## 7. 입력 전용·스코프 CSS

- 분석/추천/통계성 텍스트 최소화 유지.
- `inject_form_kit_v2_css(scope_id)`로 페이지별 스코프 격리.
- "➕ 추가"·"🗑️ 삭제"는 각 블록/행 내 UX로 유지 (menu/ingredient List 수정·삭제, recipe 행별 수정·삭제 등).

---

## 8. 검증 요약

| 항목 | menu_input | ingredient_input | recipe_management | inventory_input |
|------|------------|------------------|-------------------|-----------------|
| 기능/로직/DB/계산/저장순서 변경 | ✗ | ✗ | ✗ | ✗ |
| 위젯 key 변경 | ✗ | ✗ | ✗ | ✗ |
| ActionBar(또는 액션 블록) 1곳 | ✓ | ✓ | ✓ | ✓ |
| 중간 저장 버튼 0개 | ✓ | ✓ | ✓ | ✓ |
| FormKit v2 스코프 격리 | ✓ | ✓ | ✓ | ✓ |
