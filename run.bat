@echo off
chcp 65001 > nul
title 매장 운영 시스템 실행기

echo =====================================
echo   매장 운영 시스템 실행 중...
echo =====================================
echo.

REM 현재 bat 파일이 있는 폴더로 이동
cd /d "%~dp0"

REM 가상환경 없으면 생성
if not exist ".venv" (
    echo [1/4] 가상환경 생성 중...
    python -m venv .venv
)

REM 가상환경 활성화
echo [2/4] 가상환경 활성화...
call .venv\Scripts\activate

REM pip 업그레이드
echo [3/4] 필수 패키지 설치 중...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Streamlit 실행
echo [4/4] 매장 운영 시스템 실행!
echo.
streamlit run app.py

pause
