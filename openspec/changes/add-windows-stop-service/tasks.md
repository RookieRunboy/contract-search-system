1. Add `stop_windows.ps1` to terminate the backend PID from `logs/backend.pid`, handle missing/invalid PIDs gracefully, and optionally stop the Docker `es` container.
2. Document NSSM and WinSW service setup examples for running the backend (`uvicorn`/`contractApi.py`) with auto-restart on Windows, noting log paths and ports.
3. Smoke check new script locally (PowerShell parsing) and ensure docs link to the script; no changes to Linux scripts.
