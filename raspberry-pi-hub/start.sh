#!/bin/bash
# Quick start script for Raspberry Pi Hub

# Set DISPLAY if not already set (for GUI)
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

# Navigate to script directory
cd "$(dirname "$0")"

# Start the application
python3 main.py
