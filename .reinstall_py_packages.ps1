Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Activating virtual environment..." -ForegroundColor Green
. venv/Scripts/activate

Write-Host "Installing/updating packages from high-requirements.txt..." -ForegroundColor Yellow
pip install -r high-requirements.txt

Write-Host "Freezing current package versions to requirements.txt..." -ForegroundColor Yellow
pip freeze > requirements.txt

Write-Host "Package version update completed successfully!" -ForegroundColor Green