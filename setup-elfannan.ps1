$ErrorActionPreference = "Stop"

$Project = "D:\ElFannan"

Write-Host "=== Setting up ElFannan ===" -ForegroundColor Cyan

# ------------------------------------------------------------
# 1. Check prerequisites
# ------------------------------------------------------------

$missing = @()

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    $missing += "Git"
}

try {
    & py -3.12 --version *> $null
    if ($LASTEXITCODE -ne 0) {
        $missing += "Python 3.12"
    }
}
catch {
    $missing += "Python 3.12"
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $missing += "FFmpeg"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $missing += "uv"
}

if ($missing.Count -gt 0) {
    throw ("Missing prerequisites: " + ($missing -join ", "))
}

# ------------------------------------------------------------
# 2. Create project directories
# ------------------------------------------------------------

$dirs = @(
    "$Project\src\elfannan",
    "$Project\config",
    "$Project\artists\_template",
    "$Project\assets\audio",
    "$Project\assets\models",
    "$Project\data\input",
    "$Project\data\stems",
    "$Project\data\voices",
    "$Project\data\lyrics",
    "$Project\data\music",
    "$Project\data\output",
    "$Project\logs",
    "$Project\scripts",
    "$Project\engines",
    "$Project\kaggle",
    "$Project\.cache\huggingface\hub",
    "$Project\.cache\huggingface\datasets",
    "$Project\.cache\torch",
    "$Project\.cache\uv",
    "$Project\.cache\pip"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# ------------------------------------------------------------
# 3. Move caches to D:
# ------------------------------------------------------------

[Environment]::SetEnvironmentVariable(
    "HF_HOME",
    "$Project\.cache\huggingface",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "HF_HUB_CACHE",
    "$Project\.cache\huggingface\hub",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "HF_DATASETS_CACHE",
    "$Project\.cache\huggingface\datasets",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "TORCH_HOME",
    "$Project\.cache\torch",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "UV_CACHE_DIR",
    "$Project\.cache\uv",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "PIP_CACHE_DIR",
    "$Project\.cache\pip",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "XDG_CACHE_HOME",
    "$Project\.cache",
    "User"
)

# Also set them in the current PowerShell session.
$env:HF_HOME = "$Project\.cache\huggingface"
$env:HF_HUB_CACHE = "$Project\.cache\huggingface\hub"
$env:HF_DATASETS_CACHE = "$Project\.cache\huggingface\datasets"
$env:TORCH_HOME = "$Project\.cache\torch"
$env:UV_CACHE_DIR = "$Project\.cache\uv"
$env:PIP_CACHE_DIR = "$Project\.cache\pip"
$env:XDG_CACHE_HOME = "$Project\.cache"

Set-Location $Project

# ------------------------------------------------------------
# 4. Create core Python environment
# ------------------------------------------------------------

if (-not (Test-Path "$Project\.venv\Scripts\python.exe")) {
    Write-Host "Creating core virtual environment..." -ForegroundColor Yellow
    uv venv --python 3.12 "$Project\.venv"
}

# ------------------------------------------------------------
# 5. Install core dependencies
# ------------------------------------------------------------

Write-Host "Installing core Python dependencies..." -ForegroundColor Yellow

uv pip install `
    --python "$Project\.venv\Scripts\python.exe" `
    -r "$Project\requirements.txt"

uv pip install `
    --python "$Project\.venv\Scripts\python.exe" `
    -e "$Project"

# ------------------------------------------------------------
# 6. Create .env
# ------------------------------------------------------------

if (-not (Test-Path "$Project\.env")) {
    if (Test-Path "$Project\.env.example") {
        Copy-Item "$Project\.env.example" "$Project\.env"
    }
}

# ------------------------------------------------------------
# 7. Clone AI engines
# ------------------------------------------------------------

$AceStep = "$Project\engines\ace-step"
$RVC = "$Project\engines\rvc"

if (-not (Test-Path "$AceStep\.git")) {
    Write-Host "Cloning ACE-Step 1.5..." -ForegroundColor Yellow

    git clone --depth 1 `
        https://github.com/ace-step/ACE-Step-1.5.git `
        "$AceStep"
}
else {
    Write-Host "ACE-Step already exists." -ForegroundColor DarkGray
}

if (-not (Test-Path "$RVC\.git")) {
    Write-Host "Cloning RVC..." -ForegroundColor Yellow

    git clone --depth 1 `
        https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git `
        "$RVC"
}
else {
    Write-Host "RVC already exists." -ForegroundColor DarkGray
}

# ------------------------------------------------------------
# 8. Final status
# ------------------------------------------------------------

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "ElFannan setup completed." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Project : $Project"
Write-Host "Core    : $Project\.venv"
Write-Host "ACE     : $AceStep"
Write-Host "RVC     : $RVC"
Write-Host "Cache   : $Project\.cache"
Write-Host ""
Write-Host "Run the environment check next:"
Write-Host ".\scripts\check_env.ps1" -ForegroundColor Cyan
Write-Host ""
