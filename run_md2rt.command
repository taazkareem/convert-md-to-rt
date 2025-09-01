#!/bin/bash

# MD→RT Launcher Script
# Double-click this file to run MD→RT

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    echo "   You can download it from: https://www.python.org/downloads/"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "🔧 Setting up MD→RT for first use..."
    echo "   This may take a few minutes..."
    
    # Create virtual environment
    python3 -m venv .venv
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt 2>/dev/null || pip install pyobjc rumps
    
    echo "✅ Setup complete!"
else
    # Activate virtual environment
    source .venv/bin/activate
fi

echo "🚀 Starting MD→RT..."
echo "   The app will appear in your menu bar."
echo "   Copy Markdown text and paste it anywhere - it will be converted to Rich Text!"
echo ""
echo "   To stop the app, press Ctrl+C in this window or quit from the menu bar."
echo ""

# Run the app
python3 src/md2rt/menubar_debug.py
