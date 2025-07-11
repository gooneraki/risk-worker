# Script to start the application

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
. venv/Scripts/activate

# Start the application
uvicorn app.main:app --env-file .env.local --reload --port 8000 