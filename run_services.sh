#!/usr/bin/env bash

# ==============================================================================
# Credit Risk System - Multi-Platform Service Launcher (Bash)
# Supports: Linux, macOS, Windows (Git Bash / WSL / MSYS2)
# ==============================================================================

# Colorful Output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}   🚀 CREDIT RISK SYSTEM - SERVICE LAUNCHER        ${NC}"
echo -e "${CYAN}====================================================${NC}"

# 1. Detect Operating System
OS="$(uname -s 2>/dev/null || echo "Windows")"
echo -e "${YELLOW}Detected Platform:${NC} $OS"

# 2. Activate Virtual Environment Cross-Platform
VENV_PATH=""
if [ -f ".venv/Scripts/activate" ]; then
    VENV_PATH=".venv/Scripts/activate"
elif [ -f ".venv/bin/activate" ]; then
    VENV_PATH=".venv/bin/activate"
elif [ -f "venv/bin/activate" ]; then
    VENV_PATH="venv/bin/activate"
fi

if [ -n "$VENV_PATH" ]; then
    echo -e "${GREEN}✓ Activating Python virtual environment (${VENV_PATH})...${NC}"
    source "$VENV_PATH"
else
    echo -e "${RED}⚠ Warning: No Python virtual environment found (.venv or venv). Using system Python.${NC}"
fi

# 3. Function to handle clean exit on Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Stopping all running background services...${NC}"
    kill $(jobs -p) 2>/dev/null
    echo -e "${GREEN}✓ All services stopped. Goodbye!${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 4. Display Menu Options
echo ""
echo -e "${CYAN}Select an action to run:${NC}"
echo "  1) Run ALL (API Server + Web App Frontend)"
echo "  2) Run API Server only (FastAPI on http://localhost:8000)"
echo "  3) Run Web App Frontend only (Vite on http://localhost:5173)"
echo "  4) Run Data Pipeline ETL (Extract & Transform)"
echo "  5) Run ML Training Pipeline (Credit Risk)"
echo "  q) Quit"
echo ""

read -p "Enter choice [1-5 or q]: " CHOICE

case $CHOICE in
    1)
        echo -e "\n${GREEN}Starting API Server and Web App Frontend in parallel...${NC}"
        echo -e "${CYAN}API Server Docs: http://localhost:8000/docs${NC}"
        echo -e "${CYAN}Web App UI:     http://localhost:5173${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop both services.${NC}\n"

        python -m services.api_server.app.main &
        npm run dev --prefix services/web_app &
        wait
        ;;
    2)
        echo -e "\n${GREEN}Starting FastAPI API Server...${NC}"
        python -m services.api_server.app.main
        ;;
    3)
        echo -e "\n${GREEN}Starting Web App Frontend...${NC}"
        npm run dev --prefix services/web_app
        ;;
    4)
        echo -e "\n${GREEN}Executing Data Pipeline ETL (--skip-db)...${NC}"
        python -m services.data_pipeline.main --skip-db
        ;;
    5)
        echo -e "\n${GREEN}Executing ML Training Pipeline...${NC}"
        python -m services.ml_engine.src.machine_learning.pipeline --task credit_risk
        ;;
    q|Q)
        echo -e "${GREEN}Exiting.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac
