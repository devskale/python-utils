#!/bin/bash

# Function to check if Redis is running
check_redis() {
    redis-cli ping
}

# Check if Redis is running
if check_redis | grep -q PONG;
then
    echo "Redis is already running."
else
    echo "Redis is not running. Please start Redis first."
    exit 1
fi

# Start the FastAPI server in the background
echo "Starting FastAPI server..."
# Activate the virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "No virtual environment found (looked for .venv or venv). Please create one and install dependencies."
    exit 1
fi

uvicorn robotni_arq.api:app --reload &
API_PID=$!

# Start the Arq worker in the background
echo "Starting Arq worker..."
arq robotni_arq.workers.worker.WorkerSettings &
WORKER_PID=$!

echo "FastAPI server (PID: $API_PID) and Arq worker (PID: $WORKER_PID) started."

# Wait for background processes to finish (optional, depending on desired behavior)
# wait $API_PID
# wait $WORKER_PID

# To stop the processes later, you can use:
# kill $API_PID $WORKER_PID