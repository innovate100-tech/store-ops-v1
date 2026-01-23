# PDF 한글 폰트 문제 해결 방법

## 현재 상태
- 폰트 등록 기능이 추가되었습니다
- Windows 기본 폰트(malgun.ttf 등)를 자동으로 찾아 등록합니다
- 테스트 결과: 폰트 등록 성공 확인됨

## 문제가 계속되는 경우

### 1. 폰트 등록 상태 확인
프로젝트 루트에서 다음 명령 실행:
```bash
python test_font.py
```

### 2. 수동 폰트 등록 (임시 해결책)
만약 자동 등록이 실패하면, `src/reporting.py`의 `register_korean_font()` 함수를 수정하여 직접 폰트 경로를 지정할 수 있습니다:

```python
# src/reporting.py의 register_korean_font() 함수에서
# 다음 줄을 추가하거나 수정:

# 직접 폰트 경로 지정 (예시)
font_path = r"C:\Windows\Fonts\malgun.ttf"  # 실제 경로로 변경
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
    return ("KoreanFont", True, f"폰트 등록: {font_path}")
```

### 3. 프로젝트에 폰트 파일 포함
가장 확실한 방법은 프로젝트에 한글 폰트 파일을 직접 포함하는 것입니다:

1. `assets/fonts/` 폴더 생성
2. 한글 폰트 파일 복사 (예: NotoSansKR-Regular.ttf)
3. 코드가 자동으로 찾아서 사용합니다

### 4. 디버깅 정보 확인
PDF 생성 시 콘솔에 다음 메시지가 표시됩니다:
- `[PDF] 한글 폰트 등록 성공: ...` → 정상
- `[PDF] 경고: 한글 폰트를 찾을 수 없습니다...` → 문제 있음

### 5. Streamlit 로그 확인
앱 실행 시 콘솔에서 폰트 등록 관련 로그를 확인하세요.

## 추가 확인 사항

1. **폰트 파일 존재 확인**
   - `C:\Windows\Fonts\malgun.ttf` 파일이 있는지 확인
   - 파일 탐색기에서 직접 확인

2. **PDF 뷰어 확인**
   - 다른 PDF 뷰어로 열어보기 (Adobe Reader, Edge 등)
   - 일부 뷰어에서는 폰트가 제대로 표시되지 않을 수 있습니다

3. **폰트 등록 재시도**
   - 앱을 재시작하면 폰트가 다시 등록됩니다
   - 캐시 문제일 수 있으니 재시작 후 다시 시도

## 최종 해결책

위 방법들이 모두 실패하면, 다음을 시도해보세요:

1. **Noto Sans KR 폰트 다운로드 및 사용**
   - https://fonts.google.com/noto/specimen/Noto+Sans+KR
   - 다운로드 후 `assets/fonts/NotoSansKR-Regular.ttf`에 배치

2. **Pretendard 폰트 사용**
   - https://github.com/orioncactus/pretendard
   - 다운로드 후 `assets/fonts/Pretendard-Regular.ttf`에 배치

이렇게 하면 프로젝트에 폰트가 포함되어 항상 사용할 수 있습니다.
