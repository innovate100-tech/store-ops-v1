# 🎯 Supabase SQL 실행 - 초간단 가이드 (클릭만 하면 됨!)

## 📌 전체 과정 요약 (3단계)

1. **Supabase 열기** → **SQL Editor** 클릭
2. **SQL 코드 복사** → **붙여넣기**
3. **"Run" 버튼** 클릭 → 끝!

---

## 🚀 상세 단계 (화면 보면서 따라하기)

### ⭐ 1단계: Supabase 대시보드 열기

1. 브라우저 열기 (Chrome 권장)
2. 주소창에 입력: `https://app.supabase.com`
3. 로그인 (이메일 + 비밀번호)
4. **프로젝트 선택** (왼쪽 상단에 프로젝트 목록 있음)

---

### ⭐ 2단계: SQL Editor 찾기

왼쪽 메뉴에서 찾기:
```
📊 Dashboard
📝 SQL Editor  ← 이거 클릭!
📋 Table Editor
🔐 Authentication
...
```

**"SQL Editor"** 클릭하면 → 큰 텍스트 입력창이 보입니다!

---

### ⭐ 3단계: 첫 번째 SQL 실행 (RLS 정책 헬퍼)

#### 3-1. 파일 열기
1. 프로젝트 폴더에서 `sql/rls_policy_helper.sql` 파일 열기
2. **전체 선택**: `Ctrl + A` (또는 마우스로 드래그)
3. **복사**: `Ctrl + C`

#### 3-2. Supabase에 붙여넣기
1. Supabase SQL Editor의 **큰 텍스트 입력창** 클릭
2. 기존 내용 있으면 모두 삭제 (`Ctrl + A` → `Delete`)
3. **붙여넣기**: `Ctrl + V`
4. 코드가 입력창에 나타남

#### 3-3. 실행 버튼 클릭
1. 입력창 **아래쪽** 보기
2. **"Run"** 버튼 찾기 (초록색 버튼)
   - 또는 키보드: `Ctrl + Enter`
3. **"Run"** 클릭!
4. 1-2초 기다리기
5. ✅ 성공 메시지 확인: "Success" 또는 "Success. No rows returned"

#### 3-4. 정책 생성 함수 실행
1. 입력창 내용 **모두 삭제** (`Ctrl + A` → `Delete`)
2. 아래 코드 **복사해서 붙여넣기**:
   ```sql
   SELECT create_all_rls_policies();
   ```
3. **"Run"** 버튼 클릭
4. ✅ 성공 확인

---

### ⭐ 4단계: 두 번째 SQL 실행 (뷰 생성) - 선택사항

#### 4-1. 파일 열기
1. 프로젝트 폴더에서 `sql/views_from_daily_close.sql` 파일 열기
2. **전체 선택**: `Ctrl + A`
3. **복사**: `Ctrl + C`

#### 4-2. Supabase에 붙여넣기 및 실행
1. SQL Editor 입력창 클릭
2. 기존 내용 삭제 (`Ctrl + A` → `Delete`)
3. **붙여넣기**: `Ctrl + V`
4. **"Run"** 버튼 클릭
5. ✅ 성공 확인

---

## ✅ 완료 확인 방법

### RLS 정책 확인
1. 왼쪽 메뉴: **"Table Editor"** 클릭
2. 아무 테이블 선택 (예: `sales`)
3. 상단 탭에서 **"Policies"** 클릭
4. 4개의 정책이 보이면 ✅ 성공!

### 뷰 확인
1. 왼쪽 메뉴: **"Database"** 클릭
2. **"Views"** 탭 클릭
3. 다음 뷰들이 보이면 ✅ 성공:
   - `sales_from_daily_close`
   - `naver_visitors_from_daily_close`
   - `daily_sales_items_from_daily_close`

---

## 🆘 문제 해결

### "Run" 버튼이 안 보여요
- 입력창 아래로 스크롤
- 또는 `Ctrl + Enter` 키보드 단축키 사용

### 에러가 나요
- **"already exists"** 에러 → 무시해도 됨 (이미 생성된 것)
- 다른 에러 → 에러 메시지 복사해서 저장

### SQL Editor가 안 보여요
- 왼쪽 메뉴에서 **"SQL Editor"** 또는 **"SQL"** 찾기
- 프로젝트가 선택되었는지 확인

---

## 💡 핵심 포인트

1. **복사** (`Ctrl + C`) → **붙여넣기** (`Ctrl + V`) → **Run** 클릭
2. 에러가 나도 당황하지 마세요! 대부분 해결 가능합니다.
3. "already exists" 에러는 무시해도 됩니다.

---

## 🎉 끝!

이제 모든 SQL이 실행되었습니다. 
앱이 더 효율적으로 작동할 거예요! 🚀
