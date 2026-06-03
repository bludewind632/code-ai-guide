# 停止旧进程
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2

Write-Host "=== 后端启动 (端口 8000) ===" -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit','-Command','cd E:\code-ai-guide\backend; E:\code-ai-guide\backend\conda-env\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload'

Start-Sleep 5

Write-Host "=== 前端启动 (端口 3000) ===" -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit','-Command','cd E:\code-ai-guide\frontend; npm run dev'

Start-Sleep 3

Write-Host "=== 启动完成 ===" -ForegroundColor Green
Write-Host "后端: http://localhost:8000"
Write-Host "前端: http://localhost:3000"
