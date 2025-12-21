#!/bin/bash

# =================================================================
# Medical Knowledge Graph Governance Tool Startup Script
# =================================================================

# Color constants for logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Medical Knowledge Graph Governance Tool...${NC}"

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n${RED}Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Trap Ctrl+C (SIGINT) and SIGTERM
trap cleanup SIGINT SIGTERM

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: conda is not installed or not in PATH.${NC}"
    exit 1
fi

# 1. Start Backend
echo -e "${GREEN}Starting Backend (conda: medical)...${NC}"
cd backend || exit

# Use conda run to execute in the specific environment without needing to 'activate' in the shell
# This is more robust for scripts
conda run -n medical uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cd ..

# 2. Start Frontend
echo -e "${GREEN}Starting Frontend...${NC}"
cd frontend || exit

# Ensure node_modules exists, but don't run npm install by default to save time
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}node_modules not found, installing dependencies...${NC}"
    npm install
fi

npm run dev &
FRONTEND_PID=$!

cd ..

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}Services are starting up!${NC}"
echo -e "${BLUE}Backend: http://localhost:8000${NC}"
echo -e "${BLUE}Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}Press Ctrl+C to stop both services.${NC}"
echo -e "${BLUE}====================================================${NC}"

# Wait for subprocesses
wait
