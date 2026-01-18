# Streamlit 앱 실행 스크립트
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
python -m streamlit run app.py
Read-Host "Press Enter to exit"