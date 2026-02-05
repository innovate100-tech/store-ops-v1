@echo off
chcp 65001 > nul
title Next.js 매장 운영 시스템

echo =====================================
echo   Next.js 앱 실행 중...
echo =====================================
echo.

cd /d "%~dp0my-next-app"

if not exist "node_modules" (
    echo [1/2] 패키지 설치 중...
    call npm install
    echo.
)

echo [2/2] 개발 서버 실행 (http://localhost:3000)
echo.
call npm run dev

pause
