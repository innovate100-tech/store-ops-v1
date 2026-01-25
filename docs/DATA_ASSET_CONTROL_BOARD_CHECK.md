# DATA ASSET CONTROL BOARD 함수 연결 및 기준 체크 리포트

## 📋 체크 결과 요약

### ✅ 정상 연결된 항목
- 구조 자산: 메뉴, 재료, 레시피
- 운영 기록 자산: 일일 마감, QSC, 월간 정산
- 판단 기준 자산: 매출 목표, 비용 목표

### ❌ 문제 발견
1. **재고**: 하드코딩 "관리 중단" (함수 연결 없음)
2. **판단 기준 게이지**: 비용 목표 미반영 (매출 목표만 반영)

---

## 1. 🧱 구조 자산 패널

### 1.1 메뉴 ✅
- **함수**: `_get_asset_readiness()` → `menu_count`, `missing_price`
- **기준**: `menu_operable = menu_count > 0 AND missing_price == 0`
- **상태 표시**: 
  - `menu_operable` → "정상 운영"
  - `menu_count > 0` → "보완 필요"
  - 그 외 → "시작 필요"
- **게이지**: `menu_operable`이면 +33%
- **기준 명확성**: ✅ 명확

### 1.2 재료 ✅
- **함수**: `_get_asset_readiness()` → `ing_count`, `missing_cost`
- **기준**: `ing_operable = ing_count > 0 AND missing_cost == 0`
- **상태 표시**: 
  - `ing_operable` → "정상 운영"
  - `ing_count > 0` → "보완 필요"
  - 그 외 → "시작 필요"
- **게이지**: `ing_operable`이면 +33%
- **기준 명확성**: ✅ 명확

### 1.3 레시피 ✅
- **함수**: `_get_asset_readiness()` → `recipe_rate`
- **기준**: `recipe_operable = recipe_rate >= 80`
- **상태 표시**: 
  - `recipe_rate >= 80` → "정상 운영"
  - `recipe_rate > 0` → "보완 필요 (X%)"
  - 그 외 → "시작 필요"
- **게이지**: `recipe_operable`이면 +34%
- **기준 명확성**: ✅ 명확 (80% 기준)

### 1.4 재고 ❌
- **함수**: 없음 (하드코딩)
- **기준**: 없음
- **상태 표시**: 항상 "관리 중단" (회색)
- **게이지**: 반영 안됨
- **기준 명확성**: ❌ 기준 없음
- **권장 수정**: 재고 데이터 체크 함수 추가 또는 "선택 입력"으로 명시

---

## 2. 📒 운영 기록 자산 패널

### 2.1 일일 마감 ✅
- **함수**: `get_day_record_status(store_id, today)` → `has_close`
- **기준**: `has_daily_close = today_status.get("has_close", False)`
- **상태 표시**: 
  - `has_daily_close` → "정상 운영"
  - 그 외 → "시작 필요"
- **게이지**: `has_daily_close`이면 +40%
- **기준 명확성**: ✅ 명확 (오늘 날짜 기준)

### 2.2 QSC ✅
- **함수**: `_get_today_recommendations()` → `r4` (priority=4)
- **기준**: `r4["status"] == "completed"`
- **상태 표시**: 
  - `r4["status"] == "completed"` → "정상 운영"
  - 그 외 → "보완 필요"
- **게이지**: `r4["status"] == "completed"`이면 +30%
- **기준 명확성**: ✅ 명확 (completed 상태 기준)

### 2.3 월간 정산 ✅
- **함수**: `_get_today_recommendations()` → `r5` (priority=5)
- **기준**: `r5["status"] == "completed"`
- **상태 표시**: 
  - `r5["status"] == "completed"` → "정상 운영"
  - 그 외 → "보완 필요"
- **게이지**: `r5["status"] == "completed"`이면 +30%
- **기준 명확성**: ✅ 명확 (completed 상태 기준)

---

## 3. 🎯 판단 기준 자산 패널

### 3.1 매출 목표 ✅
- **함수**: `_get_asset_readiness()` → `has_target`
- **기준**: `has_target = targets 테이블에서 현재 연/월 데이터 존재 AND 목표매출 > 0`
- **상태 표시**: 
  - `has_target` → "정상 운영"
  - 그 외 → "시작 필요"
- **게이지**: `has_target`이면 +50% ❌ **문제: 비용 목표 미반영**
- **기준 명확성**: ✅ 명확

### 3.2 비용 목표 ✅
- **함수**: `_get_asset_readiness()` → `has_cost_target`
- **기준**: `has_cost_target = expense_structure 테이블에서 현재 연/월 데이터 존재`
- **상태 표시**: 
  - `has_cost_target` → "정상 운영"
  - 그 외 → "시작 필요"
- **게이지**: 반영 안됨 ❌ **문제: 게이지에 미반영**
- **기준 명확성**: ✅ 명확

---

## 🔧 수정 필요 사항

### 1. 재고 상태 체크 함수 추가 (선택)
```python
# _get_asset_readiness()에 추가
has_inventory = False
try:
    inventory_df = load_csv("inventory.csv", store_id=store_id)
    if not inventory_df.empty:
        has_inventory = True
except Exception:
    pass
return {
    ...
    "has_inventory": has_inventory
}
```

### 2. 판단 기준 게이지에 비용 목표 반영 (필수)
```python
# 현재 (문제)
target_score = 50 if assets.get('has_target') else 0

# 수정 후
target_score = 0
if assets.get('has_target'): target_score += 50
if assets.get('has_cost_target'): target_score += 50
# 또는
target_score = 50 if (assets.get('has_target') or assets.get('has_cost_target')) else 0
```

---

## 📊 게이지 계산 기준 요약

| 패널 | 항목 | 게이지 계산 | 기준 |
|------|------|------------|------|
| 구조 자산 | 메뉴 | +33% | menu_operable |
| 구조 자산 | 재료 | +33% | ing_operable |
| 구조 자산 | 레시피 | +34% | recipe_operable (>=80%) |
| 구조 자산 | 재고 | 0% | 반영 안됨 |
| 운영 기록 | 일일 마감 | +40% | has_daily_close |
| 운영 기록 | QSC | +30% | r4["status"] == "completed" |
| 운영 기록 | 월간 정산 | +30% | r5["status"] == "completed" |
| 판단 기준 | 매출 목표 | +50% | has_target |
| 판단 기준 | 비용 목표 | 0% | **미반영 (수정 필요)** |

---

## ✅ 완료 기준

- [x] 모든 항목의 함수 연결 확인
- [x] 각 항목의 기준 명확성 확인
- [x] 게이지 계산 로직 확인
- [ ] 재고 상태 체크 함수 추가 (선택)
- [ ] 판단 기준 게이지에 비용 목표 반영 (필수)
