# Phase 0 STEP 1 추가: UX 개선 (디버그 메시지 숨김)

**작성일**: 2026-01-24  
**작업자**: Phase 0 안정화 전담 엔지니어  
**문제**: 신규 계정 홈 화면에 기술적 디버그 메시지 과다 노출

---

## 🔴 발견된 문제

### 문제 1: 디버그 메시지 프로덕션 노출
**위치**: `src/storage_supabase.py` - `_load_csv_impl()` 함수  
**증상**: 
- 신규 계정 홈 화면에 "⚠️ 데이터 없음: menu_master.csv (0건)" 메시지 반복 표시
- 기술적 디버그 정보 (쿼리, store_id, RLS 정책 등) 노출
- 사용자 혼란 및 불신 야기

**원인**:
- 697-771줄: 데이터가 0건일 때 항상 디버그 정보 표시
- 개발 모드 체크 없이 항상 표시됨

---

## ✅ 수정 완료

### 수정 내용

**파일**: `src/storage_supabase.py`

**변경 사항**:
1. 디버그 메시지를 개발 모드에서만 표시
2. 프로덕션 모드에서는 조용히 빈 DataFrame 반환
3. expander 기본값을 `expanded=False`로 변경 (개발 모드에서도 접을 수 있도록)

**수정 전**:
```python
# 데이터가 0건인 경우 디버그 정보 표시 (온라인 환경에서도 표시)
if not result.data or len(result.data) == 0:
    # 온라인 환경에서도 진단 정보 표시 (항상 표시)
    import streamlit as st
    with st.expander(f"⚠️ 데이터 없음: {filename} (0건)", expanded=True):
        # ... 상세 디버그 정보
```

**수정 후**:
```python
# 데이터가 0건인 경우 처리 (Phase 0: 크래시 방지 + UX 개선)
if not result.data or len(result.data) == 0:
    # 개발 모드에서만 상세 디버그 정보 표시 (프로덕션에서는 숨김)
    if _is_dev_mode():
        import streamlit as st
        with st.expander(f"⚠️ 데이터 없음: {filename} (0건) [DEV MODE]", expanded=False):
            # ... 상세 디버그 정보
    
    # 프로덕션 모드: 디버그 메시지 숨김 (빈 DataFrame만 반환)
    # 신규 사용자는 데이터가 없는 것이 정상이므로 기술적 메시지 노출 금지
```

---

## 📊 수정 효과

### Before (신규 계정 홈 화면)
- ❌ "⚠️ 데이터 없음: menu_master.csv (0건)" 메시지 반복 표시
- ❌ 기술적 디버그 정보 (쿼리, store_id, RLS 정책) 노출
- ❌ 사용자 혼란 및 불신

### After (신규 계정 홈 화면)
- ✅ 디버그 메시지 숨김 (프로덕션 모드)
- ✅ 깔끔한 홈 화면 (데이터 없음 상태도 자연스럽게 처리)
- ✅ 개발 모드에서만 디버그 정보 접근 가능

---

## 🎯 추가 확인 사항

### store_id 불일치 문제
**증상**: 
- 현재 store_id: `fdd082b7-26d4-453d-a669-5e4fdf6120e6`
- 실제 데이터 store_id: `b06f6916-d8e2-4856-a4a4-46af104818d3`

**가능한 원인**:
1. 세션 상태 불일치 (로그인 후 store_id 갱신 안 됨)
2. user_profiles 테이블의 store_id와 실제 데이터 불일치
3. 매장 전환 후 세션 상태 미갱신

**권장 조치** (별도 작업):
- `get_current_store_id()` 함수에서 store_id 출처 확인
- 로그인 시 store_id 동기화 로직 확인
- 매장 전환 시 세션 상태 갱신 확인

**현재 상태**:
- 디버그 메시지 숨김으로 사용자 혼란 해소
- store_id 불일치 문제는 개발 모드에서만 확인 가능

---

## ✅ 완료 체크리스트

- [x] 디버그 메시지 개발 모드 전용으로 변경
- [x] 프로덕션 모드에서 조용히 빈 DataFrame 반환
- [x] expander 기본값 `expanded=False`로 변경
- [x] 샘플 데이터 접근 안전화 (`.data[0]` 체크 추가)

---

**작업 완료일**: 2026-01-24  
**다음 작업**: store_id 불일치 문제 조사 (필요 시)
