@echo off
chcp 65001 >nul
cd /d "%~dp0"
git init
git add .
git commit -m "일일 마감 입력 메뉴 제거 및 DEV MODE 코드 정리"
echo.
echo ========================================
echo Git 저장소 초기화 및 커밋 완료
echo ========================================
echo.
echo 다음 단계:
echo 1. GitHub에서 새 저장소를 생성하거나 기존 저장소 URL을 확인하세요
echo 2. 아래 명령어로 원격 저장소를 연결하세요:
echo    git remote add origin [저장소URL]
echo 3. 아래 명령어로 푸시하세요:
echo    git push -u origin main
echo.
pause
