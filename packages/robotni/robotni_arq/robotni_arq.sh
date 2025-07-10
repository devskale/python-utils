#!/bin/bash

# --- Configuration ---
APP_MODULE="robotni_arq.api:app"
WORKER_SETTINGS="robotni_arq.workers.worker.WorkerSettings"
PID_DIR="/tmp/robotni_arq_pids"
API_PID_FILE="$PID_DIR/api.pid"
WORKER_PID_FILE="$PID_DIR/worker.pid"
VENV_PATHS=(".venv" "venv")

# --- Functions ---

# Function to find PIDs by command pattern
find_pids() {
    local pattern=$1
    pgrep -f "$pattern"
}

# Function to activate virtual environment
activate_venv() {
    for venv_path in "${VENV_PATHS[@]}"; do
        if [ -d "$venv_path" ]; then
            echo "Activating virtual environment: $venv_path"
            source "$venv_path/bin/activate"
            return 0
        fi
    done
    echo "No virtual environment found (looked for ${VENV_PATHS[*]})."
    echo "Please create one and install dependencies."
    return 1
}

# Function to check if Redis is running
check_redis() {
    if ! command -v redis-cli &> /dev/null; then
        echo "redis-cli command not found. Cannot check Redis status."
        # Depending on strictness, you might want to exit here.
        # For now, we'll just warn and continue.
        return 0
    fi

    if redis-cli ping | grep -q PONG; then
        echo "Redis is running."
        return 0
    else
        echo "Redis is not running. Please start Redis first."
        return 1
    fi
}

# --- Commands ---

start() {
    echo "Starting services..."
    mkdir -p $PID_DIR

    # Check Redis
    if ! check_redis; then
        exit 1
    fi

    # Activate Venv
    if ! activate_venv; then
        exit 1
    fi

    # Start FastAPI server
    if [ -n "$(find_pids "uvicorn.*$APP_MODULE")" ]; then
        echo "FastAPI server is already running (PIDs: $(find_pids "uvicorn.*$APP_MODULE"))."
    else
        echo "Starting FastAPI server..."
        # Note: --reload starts a monitor process which then starts the actual server process.
        # The PID we get here is the monitor.
        PYTHONPATH=$(pwd) uvicorn $APP_MODULE --reload &
        echo $! > $API_PID_FILE
        echo "FastAPI server started with monitor PID: $(cat $API_PID_FILE)."
    fi

    # Start Arq worker
    if [ -n "$(find_pids "arq.*$WORKER_SETTINGS")" ]; then
        echo "Arq worker is already running (PIDs: $(find_pids "arq.*$WORKER_SETTINGS"))."
    else
        echo "Starting Arq worker..."
        PYTHONPATH=$(pwd) arq $WORKER_SETTINGS &
        echo $! > $WORKER_PID_FILE
        echo "Arq worker started with PID: $(cat $WORKER_PID_FILE)."
    fi

    echo "Services started."
}

stop() {
    echo "Stopping services..."

    # Stop FastAPI server
    local api_pids=$(find_pids "uvicorn.*$APP_MODULE")
    if [ -n "$api_pids" ]; then
        echo "Stopping FastAPI server (PIDs: $api_pids)..."
        kill $api_pids
    else
        echo "FastAPI server is not running."
    fi
    # Clean up PID file if it exists
    [ -f "$API_PID_FILE" ] && rm "$API_PID_FILE"


    # Stop Arq worker
    local worker_pids=$(find_pids "arq.*$WORKER_SETTINGS")
    if [ -n "$worker_pids" ]; then
        echo "Stopping Arq worker (PIDs: $worker_pids)..."
        kill $worker_pids
    else
        echo "Arq worker is not running."
    fi
    # Clean up PID file if it exists
    [ -f "$WORKER_PID_FILE" ] && rm "$WORKER_PID_FILE"


    echo "Services stopped."
}

status() {
    echo "Checking service status..."
    activate_venv > /dev/null 2>&1 # To ensure pgrep can find commands if they are in venv

    # FastAPI status
    local api_pids=$(find_pids "uvicorn.*$APP_MODULE")
    if [ -n "$api_pids" ]; then
        echo "FastAPI server is RUNNING (PIDs: $api_pids)."
    else
        echo "FastAPI server is STOPPED."
    fi

    # Arq worker status
    local worker_pids=$(find_pids "arq.*$WORKER_SETTINGS")
    if [ -n "$worker_pids" ]; then
        echo "Arq worker is RUNNING (PIDs: $worker_pids)."
    else
        echo "Arq worker is STOPPED."
    fi
}

# --- Main script ---

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1 # Give processes time to die
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0