# SSOT 검증 왕초보 가이드

## 📋 목차
1. [store_id 찾는 방법](#1-store_id-찾는-방법)
2. [검증 쿼리 사용법](#2-검증-쿼리-사용법)
3. [단계별 확인 방법](#3-단계별-확인-방법)

---

## 1. store_id 찾는 방법

### 방법 1: Supabase Table Editor에서 찾기 (가장 쉬움)

1. **Supabase 대시보드 접속**
   - https://supabase.com 접속
   - 프로젝트 선택

2. **Table Editor 열기**
   - 왼쪽 메뉴에서 **"Table Editor"** 클릭

3. **stores 테이블 열기**
   - 테이블 목록에서 **"stores"** 클릭
   - 표에 나오는 **"id"** 컬럼의 값이 store_id입니다
   - 예: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`

4. **복사하기**
   - id 값을 클릭하면 복사할 수 있습니다
   - 또는 직접 드래그해서 복사

---

### 방법 2: SQL Editor에서 찾기

1. **SQL Editor 열기**
   - 왼쪽 메뉴에서 **"SQL Editor"** 클릭

2. **아래 쿼리 실행**
```sql
SELECT id, name, created_at 
FROM stores 
ORDER BY created_at DESC;
```

3. **결과 확인**
   - 표에 나오는 **"id"** 컬럼의 값이 store_id입니다
   - **"name"** 컬럼으로 매장 이름도 확인할 수 있습니다

---

### 방법 3: 앱에서 확인하기 (개발자 도구)

1. **앱 실행**
   - Streamlit 앱 실행

2. **개발자 도구 열기**
   - 브라우저에서 `F12` 키 누르기
   - 또는 우클릭 → "검사" / "Inspect"

3. **Console 탭 열기**
   - 개발자 도구에서 **"Console"** 탭 클릭

4. **아래 코드 입력**
```javascript
// Streamlit의 session_state에서 store_id 확인
// (이 방법은 앱 구조에 따라 다를 수 있음)
```

**참고:** 이 방법은 앱 구조에 따라 다를 수 있으므로, 방법 1 또는 2를 권장합니다.

---

## 2. 검증 쿼리 사용법

### Step 1: store_id 찾기

위의 "방법 1" 또는 "방법 2"로 store_id를 찾아서 복사해두세요.

**예시:**
```
store_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
```

---

### Step 2: 검증 쿼리 파일 열기

1. **SQL Editor 열기**
   - Supabase 대시보드 → SQL Editor

2. **새 쿼리 작성**
   - "+ New query" 버튼 클릭

3. **쿼리 복사**
   - `sql/ssot_검증_쿼리.sql` 파일 내용 복사
   - SQL Editor에 붙여넣기

---

### Step 3: store_id 변경하기

**참고:** 파일에 `'your-store-id-here'`라고 적혀 있는 부분을 모두 찾아서 실제 store_id로 바꿔야 합니다.

**방법:**
1. SQL Editor에서 `Ctrl + F` (또는 `Cmd + F`) 누르기
2. `your-store-id-here` 검색
3. **"Replace All"** 클릭
4. 실제 store_id 입력
5. **"Replace All"** 클릭

**예시:**
```
변경 전: 'your-store-id-here'::UUID
변경 후: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::UUID
```

---

### Step 4: 쿼리 실행

1. **쿼리 선택**
   - 실행할 쿼리만 선택 (마우스로 드래그)
   - 또는 전체 선택 (`Ctrl + A`)

2. **실행**
   - **"Run"** 버튼 클릭
   - 또는 `Ctrl + Enter` (또는 `Cmd + Enter`)

3. **결과 확인**
   - 아래에 표로 결과가 나옵니다
   - 주석에 적힌 "기대 결과"와 비교해보세요

---

## 3. 단계별 확인 방법

### ✅ 1단계: 기본 확인 (가장 중요!)

**실행할 쿼리:**
```sql
-- VIEW 존재 확인
SELECT table_name 
FROM information_schema.tables
WHERE table_name IN ('v_daily_sales_official', 'v_daily_sales_best_available');
```

**기대 결과:**
- 2개 행이 나와야 합니다
- `v_daily_sales_official`
- `v_daily_sales_best_available`

**만약 0개 행이 나오면:**
- `sql/ssot_views_and_audit.sql` 파일이 제대로 실행되지 않은 것입니다
- 다시 실행해주세요

---

### ✅ 2단계: VIEW 동작 확인

**실행할 쿼리:**
```sql
-- ⚠️ 'your-store-id-here'를 실제 store_id로 변경하세요!
SELECT 
    date,
    total_sales,
    is_official,
    source
FROM v_daily_sales_best_available
WHERE store_id = 'your-store-id-here'::UUID
ORDER BY date DESC
LIMIT 5;
```

**기대 결과:**
- 데이터가 있으면 표가 나옵니다
- `is_official` 컬럼: `true` 또는 `false`
- `source` 컬럼: `'daily_close'` 또는 `'sales'`

**만약 에러가 나오면:**
- store_id가 잘못되었을 수 있습니다
- store_id를 다시 확인해주세요

---

### ✅ 3단계: SSOT 분리 확인 (핵심!)

**실행할 쿼리:**
```sql
-- ⚠️ 'your-store-id-here'를 실제 store_id로 변경하세요!

-- sales만 있는 날짜 확인
SELECT 
    s.date,
    (SELECT COUNT(*) FROM v_daily_sales_official WHERE store_id = s.store_id AND date = s.date) AS official_count,
    (SELECT COUNT(*) FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date) AS best_count,
    (SELECT is_official FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date LIMIT 1) AS best_is_official
FROM sales s
WHERE s.store_id = 'your-store-id-here'::UUID
  AND NOT EXISTS (
      SELECT 1 FROM daily_close dc 
      WHERE dc.store_id = s.store_id AND dc.date = s.date
  )
ORDER BY s.date DESC
LIMIT 5;
```

**기대 결과:**
- `official_count` = `0` (공식 뷰에는 없음)
- `best_count` = `1` (최선 뷰에는 있음)
- `best_is_official` = `false` (공식 아님)

**이게 맞으면 SSOT가 제대로 작동하는 것입니다!**

---

### ✅ 4단계: Audit 확인

**실행할 쿼리:**
```sql
-- ⚠️ 'your-store-id-here'를 실제 store_id로 변경하세요!
SELECT 
    date,
    action,
    old_qty,
    new_qty,
    source,
    changed_at
FROM daily_sales_items_audit
WHERE store_id = 'your-store-id-here'::UUID
ORDER BY changed_at DESC
LIMIT 10;
```

**기대 결과:**
- 최근 변경 이력 10개가 나옵니다
- `action` 컬럼: `'insert'`, `'update'`, 또는 `'soft_delete'`
- `source` 컬럼: `'close'` 또는 `'override'`

**만약 0개 행이 나오면:**
- 아직 점장 마감이나 판매량 보정을 하지 않은 것입니다
- 정상입니다 (데이터가 없으면 당연히 audit도 없음)

---

## 🎯 빠른 체크리스트

### 최소 확인 항목 (5분 안에)

1. [ ] **VIEW 2개 존재 확인**
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_name IN ('v_daily_sales_official', 'v_daily_sales_best_available');
   ```
   → 2개 행 나와야 함

2. [ ] **audit 테이블 존재 확인**
   ```sql
   SELECT COUNT(*) FROM information_schema.columns
   WHERE table_name = 'daily_sales_items_audit';
   ```
   → 11개 나와야 함

3. [ ] **VIEW 조회 테스트** (store_id 변경 필요!)
   ```sql
   SELECT * FROM v_daily_sales_best_available 
   WHERE store_id = 'your-store-id-here'::UUID 
   LIMIT 1;
   ```
   → 에러 없이 결과 나와야 함

---

## 💡 팁

### store_id를 한 번만 변경하는 방법

1. **SQL Editor에서 Find & Replace 사용**
   - `Ctrl + H` (또는 `Cmd + H`)
   - Find: `'your-store-id-here'`
   - Replace: `'실제-store-id'`
   - **"Replace All"** 클릭

2. **변수 사용 (고급)**
   - SQL Editor 상단에 변수 선언
   - 아래 쿼리에서 변수 사용
   - (이 방법은 복잡하므로 생략)

---

## ❓ 자주 묻는 질문

### Q1: store_id를 찾을 수 없어요

**A:** 
- Supabase Table Editor에서 `stores` 테이블을 열어보세요
- 또는 SQL Editor에서 `SELECT * FROM stores;` 실행

---

### Q2: 쿼리 실행 시 에러가 나요

**A:**
- store_id가 올바른지 확인하세요
- UUID 형식이 맞는지 확인하세요 (예: `'a1b2c3d4-e5f6-7890-abcd-ef1234567890'`)
- 작은따옴표(`'`)를 빼먹지 않았는지 확인하세요

---

### Q3: 결과가 0개 행이에요

**A:**
- 데이터가 없는 것이 정상일 수 있습니다
- 점장 마감을 한 번도 하지 않았다면 데이터가 없을 수 있습니다
- 테스트를 위해 점장 마감을 한 번 해보세요

---

### Q4: official_count가 0인데 best_count가 1이에요

**A:**
- **정상입니다!** 이것이 SSOT의 핵심입니다
- `sales`만 있는 날짜는 `official_count=0`, `best_count=1`이 맞습니다
- `is_official=false`로 표시되어야 합니다

---

## 📞 도움이 필요하면

문제가 발생하면 다음 정보를 확인해주세요:
1. 에러 메시지 전체
2. 실행한 쿼리
3. store_id (민감 정보이므로 마스킹 가능)
