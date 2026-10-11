# PowerShell Developer Helper for ReconPilot

function Show-Help {
    Write-Host "ReconPilot Developer Tasks:" -ForegroundColor Cyan
    Write-Host "  ./scripts/dev.ps1 install-backend   - Install Python dependencies"
    Write-Host "  ./scripts/dev.ps1 install-frontend  - Install Node dependencies"
    Write-Host "  ./scripts/dev.ps1 start-backend     - Run FastAPI development server"
    Write-Host "  ./scripts/dev.ps1 start-frontend    - Run Vite frontend dev server"
    Write-Host "  ./scripts/dev.ps1 test-backend      - Run pytest on server suite"
    Write-Host "  ./scripts/dev.ps1 lint-backend      - Run ruff check and format check"
    Write-Host "  ./scripts/dev.ps1 lint-frontend     - Run ESLint and TypeScript check"
    Write-Host "  ./scripts/dev.ps1 build-frontend    - Run production Vite build"
}

param([string]$Task = "help")

switch ($Task.ToLower()) {
    "install-backend" {
        python -m pip install -e ".[dev]"
    }
    "install-frontend" {
        Set-Location client; npm install; Set-Location ..
    }
    "start-backend" {
        python -m uvicorn app.main:app --app-dir server --reload --host 127.0.0.1 --port 8000
    }
    "start-frontend" {
        Set-Location client; npm run dev; Set-Location ..
    }
    "test-backend" {
        python -m pytest server/tests
    }
    "lint-backend" {
        python -m ruff check server; python -m ruff format server --check
    }
    "lint-frontend" {
        Set-Location client; npm run lint; npx tsc --noEmit; Set-Location ..
    }
    "build-frontend" {
        Set-Location client; npm run build; Set-Location ..
    }
    default {
        Show-Help
    }
}
