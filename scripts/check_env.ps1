$ErrorActionPreference = "Continue"
Write-Host "=== ElFannan environment check ===" -ForegroundColor Cyan
Write-Host "Project: $((Get-Location).Path)"
Write-Host ""

$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) { python --version } else { Write-Host "python: NOT FOUND" -ForegroundColor Yellow }

$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) { git --version } else { Write-Host "git: NOT FOUND" -ForegroundColor Yellow }

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) { uv --version } else { Write-Host "uv: NOT FOUND" -ForegroundColor Yellow }

$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ff) { ffmpeg -version | Select-Object -First 1 } else { Write-Host "ffmpeg: NOT FOUND" -ForegroundColor Yellow }

$nv = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nv) { nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader } else { Write-Host "nvidia-smi: NOT FOUND (normal on machines without NVIDIA GPU)" -ForegroundColor Yellow }

if (Test-Path .venv\Scripts\python.exe) {
    Write-Host ""
    Write-Host "Core venv:" -ForegroundColor Green
    .venv\Scripts\python.exe -c "import sys; print(sys.version); import numpy; print('numpy', numpy.__version__)"
}
