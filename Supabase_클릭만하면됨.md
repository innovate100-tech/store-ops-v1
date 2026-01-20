# 🎯 Supabase SQL 실행 - 클릭만 하면 됨!

## 📌 전체 과정 (3번만 클릭하면 끝!)

1. **Supabase 열기** → 왼쪽 메뉴에서 **"SQL Editor"** 클릭
2. **코드 복사** → **붙여넣기** → **"Run"** 버튼 클릭
3. 완료! ✅

---

## 🚀 단계별 상세 설명

### 1️⃣ Supabase 대시보드 열기

1. 브라우저 열기
2. 주소창에 입력: `https://app.supabase.com`
3. 로그인
4. 프로젝트 선택 (왼쪽 상단)

---

### 2️⃣ SQL Editor 열기

왼쪽 메뉴에서:
```
📝 SQL Editor  ← 이거 클릭!
```

클릭하면 → 큰 텍스트 입력창이 보입니다!

---

### 3️⃣ 첫 번째 SQL 실행 (RLS 정책 헬퍼 함수)

#### 방법 1: 파일에서 복사

1. 프로젝트 폴더에서 `바로_복사해서_사용하기.txt` 파일 열기
2. **"1단계"** 부분의 코드 전체 선택 (`Ctrl + A`)
3. 복사 (`Ctrl + C`)
4. Supabase SQL Editor 입력창에 붙여넣기 (`Ctrl + V`)
5. 입력창 아래쪽 **"Run"** 버튼 클릭 (또는 `Ctrl + Enter`)
6. ✅ "Success" 메시지 확인

#### 방법 2: 직접 입력

입력창에 아래 코드를 붙여넣기:

```sql
CREATE OR REPLACE FUNCTION create_rls_policies_for_table(
    table_name TEXT,
    store_id_column TEXT DEFAULT 'store_id'
)
RETURNS void AS $$
DECLARE
    policy_name TEXT;
BEGIN
    EXECUTE format('DROP POLICY IF EXISTS "Users can view %I from their store" ON %I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS "Users can insert %I to their store" ON %I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS "Users can update %I in their store" ON %I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS "Users can delete %I from their store" ON %I', table_name, table_name);
    
    EXECUTE format(
        'CREATE POLICY "Users can view %I from their store" ON %I FOR SELECT USING (%I = get_user_store_id())',
        table_name, table_name, store_id_column
    );
    
    EXECUTE format(
        'CREATE POLICY "Users can insert %I to their store" ON %I FOR INSERT WITH CHECK (%I = get_user_store_id())',
        table_name, table_name, store_id_column
    );
    
    EXECUTE format(
        'CREATE POLICY "Users can update %I in their store" ON %I FOR UPDATE USING (%I = get_user_store_id()) WITH CHECK (%I = get_user_store_id())',
        table_name, table_name, store_id_column, store_id_column
    );
    
    EXECUTE format(
        'CREATE POLICY "Users can delete %I from their store" ON %I FOR DELETE USING (%I = get_user_store_id())',
        table_name, table_name, store_id_column
    );
    
    RAISE NOTICE 'RLS policies created for table: %', table_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_all_rls_policies()
RETURNS void AS $$
BEGIN
    PERFORM create_rls_policies_for_table('sales');
    PERFORM create_rls_policies_for_table('naver_visitors');
    PERFORM create_rls_policies_for_table('menu_master');
    PERFORM create_rls_policies_for_table('ingredients');
    PERFORM create_rls_policies_for_table('recipes');
    PERFORM create_rls_policies_for_table('daily_sales_items');
    PERFORM create_rls_policies_for_table('inventory');
    PERFORM create_rls_policies_for_table('daily_close');
    PERFORM create_rls_policies_for_table('targets');
    PERFORM create_rls_policies_for_table('abc_history');
    PERFORM create_rls_policies_for_table('expense_structure');
    PERFORM create_rls_policies_for_table('suppliers');
    PERFORM create_rls_policies_for_table('ingredient_suppliers');
    PERFORM create_rls_policies_for_table('orders');
    
    RAISE NOTICE 'All RLS policies created successfully';
END;
$$ LANGUAGE plpgsql;
```

**"Run"** 버튼 클릭!

---

### 4️⃣ 정책 생성 함수 실행

1. 입력창 내용 **모두 삭제** (`Ctrl + A` → `Delete`)
2. 아래 코드 **붙여넣기**:

```sql
SELECT create_all_rls_policies();
```

3. **"Run"** 버튼 클릭
4. ✅ 완료!

---

### 5️⃣ 뷰 생성 (선택사항)

1. 입력창 내용 **모두 삭제**
2. `바로_복사해서_사용하기.txt` 파일의 **"3단계"** 부분 복사
3. 붙여넣기
4. **"Run"** 버튼 클릭
5. ✅ 완료!

---

## 🎯 핵심 요약

### 전체 과정 (3번 클릭)

1. **Supabase** → **SQL Editor** 클릭
2. **코드 복사** → **붙여넣기** → **"Run"** 클릭
3. 완료!

### 키보드 단축키

- **전체 선택**: `Ctrl + A`
- **복사**: `Ctrl + C`
- **붙여넣기**: `Ctrl + V`
- **실행**: `Ctrl + Enter` (또는 "Run" 버튼)

---

## ✅ 확인 방법

### RLS 정책 확인

1. 왼쪽 메뉴: **"Table Editor"** 클릭
2. 아무 테이블 선택 (예: `sales`)
3. 상단 **"Policies"** 탭 클릭
4. 4개의 정책이 보이면 ✅ 성공!

---

## 🆘 문제 해결

### "Run" 버튼이 안 보여요
- 입력창 아래로 스크롤
- 또는 `Ctrl + Enter` 키보드 사용

### 에러가 나요
- **"already exists"** → 무시해도 됨 (이미 생성된 것)
- 다른 에러 → 에러 메시지 복사해서 저장

### SQL Editor가 안 보여요
- 왼쪽 메뉴에서 **"SQL Editor"** 찾기
- 프로젝트 선택 확인

---

## 💡 팁

- 코드는 `바로_복사해서_사용하기.txt` 파일에 준비되어 있습니다
- 복사 → 붙여넣기 → Run 클릭만 하면 됩니다!
- 에러가 나도 당황하지 마세요. 대부분 해결 가능합니다.

---

## 🎉 끝!

이제 모든 SQL이 실행되었습니다! 🚀
