#!/bin/bash
# Installation script for Raspberry Pi Hub on Raspberry Pi OS

echo "========================================"
echo "Raspberry Pi Hub - Installation"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi
echo ""

# Check for pip
echo "Checking for pip3..."
pip3 --version
if [ $? -ne 0 ]; then
    echo "Installing pip3..."
    sudo apt update
    sudo apt install -y python3-pip
fi
echo ""

# Check for tkinter
echo "Checking for tkinter..."
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing python3-tk..."
    sudo apt update
    sudo apt install -y python3-tk
fi
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

# Make main.py executable
chmod +x main.py
echo "Made main.py executable"
echo ""

echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "To start the application, run:"
echo "  python3 main.py"
echo ""
echo "or"
echo "  ./main.py"
echo ""
echo "For more information, see README.md"
