#!/bin/bash

# Chatmux Server Management Script
# Usage: ./manage-servers.sh [start|stop|restart|status]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/web"
BACKEND_PID_FILE="$SCRIPT_DIR/.chatmux-backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/.chatmux-frontend.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Function to start the backend server
start_backend() {
    echo -e "${YELLOW}Starting backend server...${NC}"

    if is_running "$BACKEND_PID_FILE"; then
        echo -e "${GREEN}Backend server is already running.${NC}"
        return 0
    fi

    cd "$BACKEND_DIR"

    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        uv venv
    fi

    # Start the backend server
    nohup uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    local pid=$!
    echo $pid > "$BACKEND_PID_FILE"

    # Wait a moment to check if it started successfully
    sleep 2
    if is_running "$BACKEND_PID_FILE"; then
        echo -e "${GREEN}Backend server started successfully (PID: $pid)${NC}"
        echo -e "${GREEN}Backend available at: http://localhost:8000${NC}"
    else
        echo -e "${RED}Failed to start backend server${NC}"
        return 1
    fi
}

# Function to start the frontend server
start_frontend() {
    echo -e "${YELLOW}Starting frontend server...${NC}"

    if is_running "$FRONTEND_PID_FILE"; then
        echo -e "${GREEN}Frontend server is already running.${NC}"
        return 0
    fi

    cd "$FRONTEND_DIR"

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi

    # Start the frontend server
    nohup npm run dev > frontend.log 2>&1 &
    local pid=$!
    echo $pid > "$FRONTEND_PID_FILE"

    # Wait a moment to check if it started successfully
    sleep 3
    if is_running "$FRONTEND_PID_FILE"; then
        echo -e "${GREEN}Frontend server started successfully (PID: $pid)${NC}"
        echo -e "${GREEN}Frontend available at: http://localhost:5173${NC}"
    else
        echo -e "${RED}Failed to start frontend server${NC}"
        return 1
    fi
}

# Function to stop the backend server
stop_backend() {
    echo -e "${YELLOW}Stopping backend server...${NC}"

    if is_running "$BACKEND_PID_FILE"; then
        local pid=$(cat "$BACKEND_PID_FILE")
        kill $pid
        rm -f "$BACKEND_PID_FILE"
        echo -e "${GREEN}Backend server stopped.${NC}"
    else
        echo -e "${YELLOW}Backend server is not running.${NC}"
    fi
}

# Function to stop the frontend server
stop_frontend() {
    echo -e "${YELLOW}Stopping frontend server...${NC}"

    if is_running "$FRONTEND_PID_FILE"; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        kill $pid
        rm -f "$FRONTEND_PID_FILE"
        echo -e "${GREEN}Frontend server stopped.${NC}"
    else
        echo -e "${YELLOW}Frontend server is not running.${NC}"
    fi
}

# Function to show status
show_status() {
    echo -e "${YELLOW}Chatmux Server Status:${NC}"
    echo -e "${YELLOW}----------------------${NC}"

    if is_running "$BACKEND_PID_FILE"; then
        local pid=$(cat "$BACKEND_PID_FILE")
        echo -e "${GREEN}Backend:  Running (PID: $pid)${NC}"
        echo -e "          http://localhost:8000"
    else
        echo -e "${RED}Backend:  Not running${NC}"
    fi

    if is_running "$FRONTEND_PID_FILE"; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "${GREEN}Frontend: Running (PID: $pid)${NC}"
        echo -e "          http://localhost:5173"
    else
        echo -e "${RED}Frontend: Not running${NC}"
    fi
}

# Function to show logs
show_logs() {
    local server=$1
    case $server in
        backend)
            if [ -f "$BACKEND_DIR/backend.log" ]; then
                echo -e "${YELLOW}Backend logs:${NC}"
                tail -n 50 "$BACKEND_DIR/backend.log"
            else
                echo -e "${RED}No backend logs found${NC}"
            fi
            ;;
        frontend)
            if [ -f "$FRONTEND_DIR/frontend.log" ]; then
                echo -e "${YELLOW}Frontend logs:${NC}"
                tail -n 50 "$FRONTEND_DIR/frontend.log"
            else
                echo -e "${RED}No frontend logs found${NC}"
            fi
            ;;
        all)
            show_logs backend
            echo ""
            show_logs frontend
            ;;
        *)
            echo -e "${RED}Usage: $0 logs [backend|frontend|all]${NC}"
            ;;
    esac
}

# Main script logic
case "$1" in
    start)
        start_backend
        start_frontend
        echo -e "${GREEN}All servers started!${NC}"
        echo -e "${YELLOW}Access Chatmux at: http://localhost:5173${NC}"
        ;;
    stop)
        stop_frontend
        stop_backend
        echo -e "${GREEN}All servers stopped.${NC}"
        ;;
    restart)
        stop_frontend
        stop_backend
        sleep 2
        start_backend
        start_frontend
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-all}"
        ;;
    backend)
        case "$2" in
            start) start_backend ;;
            stop) stop_backend ;;
            restart) stop_backend; sleep 1; start_backend ;;
            *) echo -e "${RED}Usage: $0 backend [start|stop|restart]${NC}" ;;
        esac
        ;;
    frontend)
        case "$2" in
            start) start_frontend ;;
            stop) stop_frontend ;;
            restart) stop_frontend; sleep 1; start_frontend ;;
            *) echo -e "${RED}Usage: $0 frontend [start|stop|restart]${NC}" ;;
        esac
        ;;
    *)
        echo -e "${YELLOW}Chatmux Server Management Script${NC}"
        echo -e "${YELLOW}================================${NC}"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  start              Start both backend and frontend servers"
        echo "  stop               Stop both servers"
        echo "  restart            Restart both servers"
        echo "  status             Show server status"
        echo "  logs [server]      Show server logs (backend|frontend|all)"
        echo "  backend [action]   Manage backend server (start|stop|restart)"
        echo "  frontend [action]  Manage frontend server (start|stop|restart)"
        echo ""
        echo "Examples:"
        echo "  $0 start           # Start all servers"
        echo "  $0 stop            # Stop all servers"
        echo "  $0 status          # Check server status"
        echo "  $0 logs            # Show logs from both servers"
        echo "  $0 backend start   # Start only backend"
        echo "  $0 frontend stop   # Stop only frontend"
        exit 1
        ;;
esac
