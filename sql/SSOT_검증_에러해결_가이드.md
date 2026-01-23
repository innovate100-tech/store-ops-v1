# SSOT 검증 쿼리 에러 해결 가이드

## 🚨 자주 발생하는 에러

### 에러 1: syntax error at or near "-"

**에러 메시지:**
```
ERROR: 42601: syntax error at or near "-" 
LINE 23: id AS b06f6916-d8e2-4856-a4a4-46af104818d3,
```

**원인:**
- `AS` 뒤에 UUID 값을 넣으셨습니다
- `AS` 뒤에는 컬럼 별칭(이름)만 와야 합니다

**잘못된 예:**
```sql
SELECT 
    id AS b06f6916-d8e2-4856-a4a4-46af104818d3,  -- ❌ 잘못됨!
    name AS 매장명
FROM stores;
```

**올바른 예:**
```sql
SELECT 
    id AS store_id,  -- ✅ 이게 맞습니다!
    name AS 매장명
FROM stores;
```

**해결 방법:**
1. `AS` 뒤의 UUID 값을 `store_id`로 되돌리세요
2. UUID는 `WHERE` 절에서만 사용합니다:
   ```sql
   WHERE store_id = 'b06f6916-d8e2-4856-a4a4-46af104818d3'::UUID
   ```

---

## 📝 올바른 사용법

### Step 1: store_id 찾기 (수정 금지!)

```sql
-- 이 쿼리는 그대로 실행하세요! 수정하지 마세요!
SELECT 
    id AS store_id,  -- ⬅️ "store_id"는 컬럼 이름일 뿐입니다!
    name AS 매장명,
    created_at AS 생성일
FROM stores
ORDER BY created_at DESC;
```

**결과:**
- 표에 `store_id`, `매장명`, `생성일` 컬럼이 나옵니다
- `store_id` 컬럼의 값이 실제 store_id입니다
- 이 값을 복사하세요!

---

### Step 2: store_id를 쿼리에 넣기

**찾은 store_id 예시:**
```
b06f6916-d8e2-4856-a4a4-46af104818d3
```

**WHERE 절에 넣기:**
```sql
-- ⚠️ 여기만 수정하세요!
WHERE store_id = 'b06f6916-d8e2-4856-a4a4-46af104818d3'::UUID
```

**주의사항:**
- 작은따옴표(`'`)로 감싸야 합니다
- 끝에 `::UUID`를 붙여야 합니다
- `AS` 뒤가 아닌 `WHERE` 절에 넣습니다!

---

## ✅ 올바른 예시

### 예시 1: store_id 찾기 (수정 없음)

```sql
SELECT 
    id AS store_id,  -- ✅ 이대로 두세요!
    name AS 매장명
FROM stores;
```

**결과:**
| store_id | 매장명 |
|----------|--------|
| b06f6916-d8e2-4856-a4a4-46af104818d3 | 우리 매장 |

→ `store_id` 컬럼의 값 `b06f6916-d8e2-4856-a4a4-46af104818d3`을 복사하세요!

---

### 예시 2: store_id 사용하기 (WHERE 절에 넣기)

```sql
-- ⚠️ 'your-store-id-here'를 실제 store_id로 변경하세요!
SELECT * 
FROM v_daily_sales_best_available
WHERE store_id = 'b06f6916-d8e2-4856-a4a4-46af104818d3'::UUID;
```

**변경 방법:**
1. `'your-store-id-here'` 찾기 (`Ctrl + F`)
2. `'b06f6916-d8e2-4856-a4a4-46af104818d3'`로 변경
3. 작은따옴표와 `::UUID`는 그대로 두세요!

---

## 🔍 Find & Replace 올바른 사용법

### ❌ 잘못된 방법

```
Find: your-store-id-here
Replace: b06f6916-d8e2-4856-a4a4-46af104818d3
```

**문제:** `AS` 뒤까지 바뀌어서 에러 발생!

---

### ✅ 올바른 방법

```
Find: 'your-store-id-here'::UUID
Replace: 'b06f6916-d8e2-4856-a4a4-46af104818d3'::UUID
```

**또는:**

```
Find: your-store-id-here
Replace: b06f6916-d8e2-4856-a4a4-46af104818d3
```

**단, `AS` 뒤는 건드리지 마세요!**

---

## 💡 체크리스트

수정 전 확인:
- [ ] `AS store_id`는 그대로 두었나요?
- [ ] `WHERE store_id = 'your-store-id-here'::UUID`만 수정했나요?
- [ ] 작은따옴표(`'`)를 빼먹지 않았나요?
- [ ] `::UUID`를 빼먹지 않았나요?

---

## 🆘 에러가 계속 나면

1. **전체 쿼리 복사**
   - `sql/SSOT_빠른_검증_쿼리.sql` 파일 다시 열기
   - 전체 내용 복사

2. **SQL Editor에 붙여넣기**
   - 새 쿼리 작성
   - 붙여넣기

3. **Find & Replace 사용**
   - `Ctrl + H`
   - Find: `'your-store-id-here'`
   - Replace: `'실제-store-id-값'` (작은따옴표 포함!)
   - **"Replace All"** 클릭

4. **`AS store_id`는 절대 건드리지 마세요!**
