#!/usr/bin/env bash
# Bash Developer Helper for ReconPilot

set -e

show_help() {
  echo "ReconPilot Developer Tasks:"
  echo "  ./scripts/dev.sh install-backend   - Install Python dependencies"
  echo "  ./scripts/dev.sh install-frontend  - Install Node dependencies"
  echo "  ./scripts/dev.sh start-backend     - Run FastAPI development server"
  echo "  ./scripts/dev.sh start-frontend    - Run Vite frontend dev server"
  echo "  ./scripts/dev.sh test-backend      - Run pytest on server suite"
  echo "  ./scripts/dev.sh lint-backend      - Run ruff check and format check"
  echo "  ./scripts/dev.sh lint-frontend     - Run ESLint and TypeScript check"
  echo "  ./scripts/dev.sh build-frontend    - Run production Vite build"
}

TASK="${1:-help}"

case "$TASK" in
  install-backend)
    python -m pip install -e ".[dev]"
    ;;
  install-frontend)
    cd client && npm install && cd ..
    ;;
  start-backend)
    python -m uvicorn app.main:app --app-dir server --reload --host 127.0.0.1 --port 8000
    ;;
  start-frontend)
    cd client && npm run dev && cd ..
    ;;
  test-backend)
    python -m pytest server/tests
    ;;
  lint-backend)
    python -m ruff check server && python -m ruff format server --check
    ;;
  lint-frontend)
    cd client && npm run lint && npx tsc --noEmit && cd ..
    ;;
  build-frontend)
    cd client && npm run build && cd ..
    ;;
  *)
    show_help
    ;;
esac
