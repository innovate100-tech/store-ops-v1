# P5 Phase 1 — FORM형 5개 확장 보고서

**작성일**: 2026-01-25  
**기준 레퍼런스**: `settlement_actual.py` (FormKit v2 + 블록 리듬)  
**목표**: 입력센터 FORM형 5페이지를 동일 제품 규격으로 확장

---

## 1. 변경 파일 리스트

### 완료 적용
| 파일 | 변경 요약 |
|------|-----------|
| `src/ui/components/form_kit_v2.py` | `ps_primary_ratio_input`에 `compact` 옵션 추가 |
| `ui_pages/target_cost_structure.py` | FormKit v2 + `ps_input_block` 블록 리듬, 인라인 저장 제거, ActionBar 단일 저장 |
| `ui_pages/target_sales_structure.py` | FormKit v2 + 블록 리듬, 비율 입력 compact, 합계 검증 `ps_inline_feedback` |
| `ui_pages/sales_entry.py` | STEP 3 — 단일/일괄 블록 분리, money/quantity/date FormKit v2, G2, ActionBar만 저장 |
| `ui_pages/sales_volume_entry.py` | STEP 4 — 날짜 블록, 판매량 FormKit v2, ActionBar 1개 |
| `ui_pages/daily_input_hub.py` | STEP 5 — 탭 유지, money/quantity/note FormKit, 탭 내부 버튼 제거, ActionBar만 |

---

## 2. Primary 지정 항목 목록

### target_cost_structure.py
- **Primary 1개**: 목표 월매출 (`target_cost_structure_target_sales_input`) — Block 2
- 기간 선택: Secondary (Block 1)
- 비용 구조 입력: 전부 `compact=True` (Block 3)

### target_sales_structure.py
- **Primary 1개**: 목표 월매출 (`target_sales_structure_target_sales_input`) — Block 2
- 기간 선택: Secondary (Block 1)
- 메뉴/시간대 비율: compact ratio (Block 3)

---

## 3. grep 증거: `key=` 변경 없음

### target_cost_structure.py
```
key="target_cost_structure_expense_year"
key="target_cost_structure_expense_month"
key="target_cost_structure_target_sales_input"
key=f"edit_name_{category}_{item['id']}"
key=f"edit_amount_{category}_{item['id']}"
key=f"edit_rate_{category}_{item['id']}"
key=f"cancel_edit_{category}_{item['id']}"
key=f"edit_btn_{category}_{item['id']}"
key=f"del_{category}_{item['id']}"
key=f"new_item_name_{category}_{...}"
key=f"new_amount_{category}_{...}"
key=f"new_rate_{category}_{...}"
key=f"add_{category}"
```
- 인라인 `💾 저장` 버튼(`save_edit_*`) 제거 → ActionBar `target_cost_edit_save`로 통합. 기존 입력/수정/삭제/추가 키 유지.

### target_sales_structure.py
```
key="target_sales_structure_year"
key="target_sales_structure_month"
key="target_sales_structure_target_sales_input"
key=f"menu_ratio_{cat}"
key="time_ratio_점심"
key="time_ratio_저녁"
key="time_ratio_기타"
```

### sales_entry.py
- `sales_entry_sales_category`, `sales_input_mode`, `sales_date`, `sales_store`, `sales_card`, `sales_cash`, `sales_entry_visitors`
- `visitor_date`, `visitor_count`, `sales_entry_visitor_input_mode`, `close_sales_message`
- 일괄: `batch_sales_*`, `batch_visitor_*` (render_sales_batch_input / render_visitor_batch_input)
- st.form 제거, 인라인 저장 버튼 없음. ActionBar만 저장.

### sales_volume_entry.py
- `sales_volume_entry_daily_sales_full_date`, `sales_volume_entry_daily_sales_full_{menu_name}`, `sales_volume_entry_close_msg`

### daily_input_hub.py
- `daily_input_hub_date`, `daily_input_card_sales`, `daily_input_cash_sales`, `daily_input_visitors`
- `daily_input_sales_item_{menu_name}_{selected_date}`, `daily_input_memo`
- 탭 내부 `temp_save_*` 버튼 제거. ActionBar만.

---

## 4. ActionBar 1회 렌더 근거

### target_cost_structure.py
- **위치**: `render_target_cost_structure()` 내 `render_form_layout(..., action_primary=..., action_secondary=..., main_content=...)` 호출 (1회)
- 저장 CTA: `action_primary` — 수정 모드 시 `"저장 (수정)"` + `_target_cost_save_edit`, 기본 시 `"목표 저장"` + `_target_cost_save_target_sales`
- `action_secondary`: `"전월 데이터 복사"` + `_target_cost_copy_prev_month`
- 페이지 내 중간 저장 버튼 없음. `➕ 추가` / `🗑️` / `❌ 취소` 만 블록 하단·우측 유지.

### target_sales_structure.py
- **위치**: `render_target_sales_structure()` 내 `render_form_layout(..., action_primary=..., action_secondary=..., main_content=...)` 호출 (1회)
- `action_primary`: `"목표 저장"` + `_target_sales_save_target_sales`
- `action_secondary`: `"매출 구조 저장"` + `_target_sales_save_structure`

---

## 5. 입력 전용 기준 체크리스트

| 항목 | target_cost | target_sales | sales_entry | sales_volume | daily_hub |
|------|-------------|--------------|-------------|--------------|-----------|
| 기능/로직/DB/저장순서/session_state 구조 변경 금지 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 위젯 `key` 변경 금지 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 저장 CTA는 ActionBar 하단 1곳만 | ✅ | ✅ | ✅ | ✅ | ✅ |
| `➕ 추가` 블록 하단 유지 | ✅ | N/A | N/A | N/A | N/A |
| `🗑️ 삭제` 항목 블록 우측 유지 | ✅ | N/A | N/A | N/A | N/A |
| FormKit v2 스코프 격리 (`inject_form_kit_v2_css`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Primary 1~2개 | ✅ (1개) | ✅ (1개) | ✅ | ✅ | ✅ |
| 입력 전용 원칙 (분석/리포트 UI 부활 금지) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ps_input_block` / 블록 리듬 | ✅ | ✅ | ✅ | ✅ | ✅ (탭) |

---

## 6. 스코프 CSS 유지

- `inject_form_kit_v2_css("target_cost_structure")` / `inject_form_kit_v2_css("target_sales_structure")` / `inject_form_kit_v2_css("sales_entry")` / `inject_form_kit_v2_css("sales_volume_entry")` / `inject_form_kit_v2_css("daily_input_hub")` 사용
- FormKit v2 CSS는 `[data-ps-scope]` 하위만 적용
- 공통 레이아웃(`render_form_layout`) CSS와 병행, 페이지별 스코프 유지

---

## 7. STEP 3·4·5 완료

- **STEP 3** `sales_entry`: 단일/일괄 블록 분리, money/quantity/date FormKit v2, G2, `ps_inline_feedback` 1줄, ActionBar만 저장 ✅
- **STEP 4** `sales_volume_entry`: 날짜 블록, 판매량 FormKit v2, ActionBar 1개 ✅
- **STEP 5** `daily_input_hub`: 탭 유지, 매출/방문자/메모 FormKit 교체, 탭 내부 "💾 임시 저장" 제거, 임시저장/마감 ActionBar만 ✅
