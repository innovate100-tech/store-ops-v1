# Next.js 앱 실행 스크립트
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location -Path (Join-Path $root "my-next-app")

if (-not (Test-Path "node_modules")) {
    Write-Host "[1/2] 패키지 설치 중..."
    npm install
}
Write-Host "[2/2] 개발 서버 실행 (http://localhost:3000)"
npm run dev
Read-Host "Press Enter to exit"
