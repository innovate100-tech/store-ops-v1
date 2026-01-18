@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Git 저장소 초기화 및 커밋
echo ========================================
echo.

REM .git 폴더가 있으면 삭제
if exist .git (
    echo 기존 .git 폴더 삭제 중...
    rmdir /s /q .git
)

REM Git 저장소 초기화
echo Git 저장소 초기화 중...
git init
if errorlevel 1 (
    echo 오류: git init 실패
    pause
    exit /b 1
)

REM 파일 추가
echo.
echo 파일을 스테이징 중...
git add .
if errorlevel 1 (
    echo 오류: git add 실패
    pause
    exit /b 1
)

REM 상태 확인
echo.
echo 현재 상태:
git status

REM 초기 커밋
echo.
echo 초기 커밋 생성 중...
git commit -m "Initial commit: 매장 운영 시스템 v1"
if errorlevel 1 (
    echo 오류: git commit 실패 (변경사항이 없을 수 있습니다)
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ Git 저장소 초기화 완료!
echo ========================================
echo.
echo 다음 단계:
echo 1. GitHub에서 새 저장소를 생성하세요
echo 2. 다음 명령어를 실행하세요:
echo    git remote add origin https://github.com/사용자명/저장소명.git
echo    git branch -M main
echo    git push -u origin main
echo.
pause
