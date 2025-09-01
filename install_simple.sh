#!/bin/bash

# MD→RT Simple Installer
# This script sets up MD→RT and creates a desktop shortcut

set -e

echo "🚀 MD→RT Simple Installer"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installer only works on macOS"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_status "Installing MD→RT to: $SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    echo "   You can download it from: https://www.python.org/downloads/"
    echo "   Or install via Homebrew: brew install python"
    exit 1
fi

print_success "Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
print_status "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

print_success "Dependencies installed"

# Create desktop shortcut
print_status "Creating desktop shortcut..."

# Create a simple launcher script on desktop
DESKTOP_DIR="$HOME/Desktop"
LAUNCHER_PATH="$DESKTOP_DIR/MD→RT.command"

cat > "$LAUNCHER_PATH" << 'EOF'
#!/bin/bash

# MD→RT Desktop Launcher
# This script runs MD→RT from your desktop

# Get the directory where MD→RT is installed
MD2RT_DIR="/Users/talibkareem/Code/Projects/Utilities/convert-md-to-rt"

# Change to the MD→RT directory
cd "$MD2RT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Run the app
python3 src/md2rt/menubar_debug.py
EOF

# Make the launcher executable
chmod +x "$LAUNCHER_PATH"

print_success "Desktop shortcut created: $LAUNCHER_PATH"

# Test the installation
print_status "Testing installation..."
if python3 -c "import rumps, AppKit" 2>/dev/null; then
    print_success "Installation test passed!"
else
    print_error "Installation test failed. Please check the error messages above."
    exit 1
fi

echo ""
print_success "🎉 MD→RT installation complete!"
echo ""
echo "📋 To use MD→RT:"
echo "   1. Double-click 'MD→RT.command' on your Desktop"
echo "   2. The app will appear in your menu bar"
echo "   3. Copy Markdown text and paste it anywhere - it will be converted to Rich Text!"
echo ""
echo "💡 Pro tip: You can also run it from the terminal:"
echo "   cd $SCRIPT_DIR && ./run_md2rt.command"
echo ""
echo "🚫 To uninstall: Simply delete the 'MD→RT.command' file from your Desktop"
echo ""
