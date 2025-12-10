#!/bin/bash
# Quick start script for Linux/Mac

echo "============================================================"
echo " Raahi AI Backend API Server - Starting..."
echo "============================================================"
echo

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "../venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: pip install -r ../requirements.txt"
    exit 1
fi

# Activate virtual environment
source ../venv/bin/activate

# Check if .env exists
if [ ! -f "../../.env" ]; then
    echo "[WARNING] .env file not found in project root!"
    echo "Please create .env file with database credentials"
    echo
fi

# Start server
python app.py

