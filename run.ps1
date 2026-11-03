# One-command run (Windows PowerShell):  powershell -ExecutionPolicy Bypass -File run.ps1
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if (-not (Test-Path data\network.json)) {
    & .\.venv\Scripts\python.exe scripts\generate_sample_network.py --out data\network.json
}
Start-Process "http://127.0.0.1:8000/compare.html"
& .\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000
