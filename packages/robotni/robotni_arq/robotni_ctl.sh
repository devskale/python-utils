#!/bin/bash

# Function to clean orphaned robotni processes
clean_orphaned_robotnis() {
    echo "Cleaning orphaned robotni processes..."
    # Find processes that are not 'arq worker' but might be related to previous runs
    # This is a placeholder and might need refinement based on actual process names
    # For example, if your arq workers run with a specific command line, you can target that.
    # For now, let's assume any 'python' process that is not 'arq worker' and is related to robotni_arq
    # needs to be considered.
    # A safer approach would be to use a PID file or a more specific process name.
    # For demonstration, we'll use a broad pgrep and then filter.
    # BE CAREFUL: This might kill unintended processes if not precise enough.
    # It's better to have a more specific way to identify orphaned processes.
    # For now, let's just kill any 'arq worker' processes that might be lingering.
    pkill -f "arq worker"
    echo "Orphaned robotni processes cleaned (if any)."
}

# Function to bring up robotni services
ups() {
    echo "Bringing up robotni services..."
    ./start.sh
    echo "Robotni services are up."
}

# Function to bring down robotni services
down() {
    echo "Bringing down robotni services..."
    pkill -f "arq worker"
    echo "Robotni services are down."
}

# Function to check the status of robotni services
status() {
    echo "Checking robotni service status..."
    pgrep -f "arq worker"
    if [ $? -eq 0 ]; then
        echo "Robotni worker processes are running."
    else
        echo "No robotni worker processes found."
    fi
}


# Main script logic
case "$1" in
    "up")
        clean_orphaned_robotnis
        ups
        ;;
    "down")
        down
        ;;
    "clean")
        clean_orphaned_robotnis
        ;;
    "status")
        status
        ;;
    *)
        echo "Usage: $0 {up|down|clean|status}"
        exit 1
        ;;
esac



exit 0