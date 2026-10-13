$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw '创建虚拟环境失败，请安装 Python 3.12 或以上版本。' }
}
& '.\.venv\Scripts\python.exe' -c "import importlib.util, sys; sys.exit(0 if all(importlib.util.find_spec(m) for m in ('fastapi', 'uvicorn', 'pydantic')) else 1)"
if ($LASTEXITCODE -ne 0) {
    & '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock
    if ($LASTEXITCODE -ne 0) { throw '依赖安装失败，请检查网络连接。' }
}
Write-Host 'ReqFlow: http://127.0.0.1:8765  (Ctrl+C 停止)'
& '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8765
