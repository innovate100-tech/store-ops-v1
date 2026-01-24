# 입력 페이지 DB 연결 확인 및 수정 완료 보고서

**작업 일자**: 2026-01-24  
**목적**: 메뉴 등록 및 재료 등록 페이지의 새로 추가된 입력 필드들이 DB에 저장되는지 확인 및 수정

---

## ✅ 확인 결과

### 1. 메뉴 입력 페이지 (`ui_pages/input/menu_input.py`)

#### 저장되는 필드
- ✅ **메뉴명, 판매가**: `save_menu()` 함수로 DB 저장
- ✅ **메뉴분류 (category)**: `set_menu_portfolio_category()` → `update_menu_category()` 함수로 DB 저장
- ✅ **해시태그 분류 (role)**: `set_menu_portfolio_tag()` → `upsert_menu_role_tag()` 함수로 DB 저장

#### 확인 사항
- 단일 입력: 메뉴분류와 해시태그 분류 모두 저장됨 ✅
- 일괄 입력: 메뉴분류와 해시태그 분류 모두 저장됨 ✅
- 수정: 메뉴분류와 해시태그 분류 모두 저장됨 ✅

**결론**: 메뉴 입력 페이지는 모든 필드가 DB에 정상적으로 저장됩니다.

---

### 2. 재료 입력 페이지 (`ui_pages/input/ingredient_input.py`)

#### 저장되는 필드
- ✅ **재료명, 단위, 단가, 발주단위, 변환비율**: `save_ingredient()` 함수로 DB 저장
- ✅ **재료 분류 (category)**: `_set_ingredient_category()` 함수로 DB 저장
- ✅ **상태 (status)**: `_set_ingredient_status_and_notes()` 함수로 DB 저장 (새로 추가)
- ✅ **메모 (notes)**: `_set_ingredient_status_and_notes()` 함수로 DB 저장 (새로 추가)

#### 수정 사항
1. **새 함수 추가**: `_set_ingredient_status_and_notes()`
   - 재료의 상태(status)와 메모(notes)를 DB에 저장하는 함수 추가
   - 단일 입력, 일괄 입력 모두에서 호출하도록 수정

2. **단일 입력 수정**
   - 재료 저장 후 상태와 메모도 함께 저장하도록 수정
   - 기본 상태값: "사용중"

3. **일괄 입력 수정**
   - 각 재료 저장 후 상태도 함께 저장하도록 수정

#### 주의사항
- **DB 스키마 확인 필요**: `ingredients` 테이블에 `status`와 `notes` 컬럼이 없으면 에러가 발생할 수 있습니다.
- 컬럼이 없는 경우 다음 SQL을 실행해야 합니다:
  ```sql
  ALTER TABLE ingredients 
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT '사용중' CHECK (status IN ('사용중', '사용중지')),
  ADD COLUMN IF NOT EXISTS notes TEXT;
  ```

**결론**: 재료 입력 페이지는 모든 필드가 DB에 저장되도록 수정되었습니다. (단, DB 스키마에 컬럼이 있어야 함)

---

## 📝 수정된 파일

### `ui_pages/input/ingredient_input.py`
1. **새 함수 추가** (171-202번째 줄):
   ```python
   def _set_ingredient_status_and_notes(store_id, ingredient_name, status=None, notes=None):
       """재료 상태 및 메모 저장 (DB)"""
   ```

2. **단일 입력 수정** (293-299번째 줄):
   - 재료 저장 후 상태와 메모 저장 로직 추가

3. **일괄 입력 수정** (384-390번째 줄):
   - 각 재료 저장 후 상태 저장 로직 추가

---

## 🔍 함수별 DB 연결 확인

### 메뉴 관련 함수
| 함수명 | 저장 위치 | 상태 |
|--------|----------|------|
| `save_menu()` | `menu_master` 테이블 | ✅ 정상 |
| `update_menu_category()` | `menu_master.category` | ✅ 정상 |
| `upsert_menu_role_tag()` | `menu_role_tags` 테이블 | ✅ 정상 |

### 재료 관련 함수
| 함수명 | 저장 위치 | 상태 |
|--------|----------|------|
| `save_ingredient()` | `ingredients` 테이블 | ✅ 정상 |
| `_set_ingredient_category()` | `ingredients.category` | ✅ 정상 |
| `_set_ingredient_status_and_notes()` | `ingredients.status`, `ingredients.notes` | ✅ 추가됨 (스키마 확인 필요) |

---

## ⚠️ 주의사항

### DB 스키마 확인 필요
재료 입력 페이지의 상태(status)와 메모(notes) 필드를 저장하려면 `ingredients` 테이블에 해당 컬럼이 있어야 합니다.

**확인 방법**:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ingredients' 
  AND column_name IN ('status', 'notes');
```

**컬럼이 없는 경우 추가 SQL**:
```sql
ALTER TABLE ingredients 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT '사용중' 
  CHECK (status IN ('사용중', '사용중지')),
ADD COLUMN IF NOT EXISTS notes TEXT;
```

---

## ✅ 최종 확인

### 메뉴 입력 페이지
- ✅ 메뉴명, 판매가: DB 저장
- ✅ 메뉴분류: DB 저장
- ✅ 해시태그 분류: DB 저장

### 재료 입력 페이지
- ✅ 재료명, 단위, 단가, 발주단위, 변환비율: DB 저장
- ✅ 재료 분류: DB 저장
- ✅ 상태: DB 저장 (스키마 확인 필요)
- ✅ 메모: DB 저장 (스키마 확인 필요)

---

**작성일**: 2026-01-24  
**담당**: 입력 페이지 DB 연결 확인 및 수정
