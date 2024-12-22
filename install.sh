#!/bin/bash

echo -e "\033[36m"
cat << "EOF"
 _____ _           _      
|  ___(_)_ __   __| |_ __ 
| |_  | | '_ \ / _` | '__|
|  _| | | | | | (_| | |   
|_|   |_|_| |_|\__,_|_|   

🔍 Interactive File Search Tool
Version: 0.1.0
EOF
echo -e "\033[0m"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to detect current shell
detect_shell() {
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/usr/bin/zsh" ] || [ "$SHELL" = "/bin/zsh" ]; then
        echo "zsh"
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/usr/bin/bash" ] || [ "$SHELL" = "/bin/bash" ]; then
        echo "bash"
    else
        echo "unknown"
    fi
}

# Detect current shell
CURRENT_SHELL=$(detect_shell)
echo -e "\n🔍 Shell Detection"
echo -e "Detected shell: $CURRENT_SHELL"

# Interactive shell selection
echo -e "\nSelect your shell configuration:"
echo "1) Zsh  (~/.zshrc)"
echo "2) Bash (~/.bashrc)"
echo "3) I don't know (auto-detect)"
read -p "Enter choice [1-3]: " shell_choice

case ${shell_choice:-3} in
    1) 
        SHELL_CONFIG="$HOME/.zshrc"
        ;;
    2) 
        SHELL_CONFIG="$HOME/.bashrc"
        ;;
    3)  
        if [ "$CURRENT_SHELL" = "zsh" ]; then
            SHELL_CONFIG="$HOME/.zshrc"
        else
            SHELL_CONFIG="$HOME/.bashrc"
        fi
        ;;
    *)  
        echo "Invalid choice. Using auto-detect."
        if [ "$CURRENT_SHELL" = "zsh" ]; then
            SHELL_CONFIG="$HOME/.zshrc"
        else
            SHELL_CONFIG="$HOME/.bashrc"
        fi
        ;;
esac

echo -e "Using shell config: $SHELL_CONFIG"

# Create config file if it doesn't exist
if [ ! -f "$SHELL_CONFIG" ]; then
    echo "Creating new config file: $SHELL_CONFIG"
    touch "$SHELL_CONFIG"
fi

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.7+"
    exit 1
fi

echo "✅ Found Python: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv "$SCRIPT_DIR/venv" || {
    echo "❌ Failed to create virtual environment"
    exit 1
}

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate" || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}

# Upgrade pip and install dependencies
echo "📥 Installing dependencies..."
python3 -m pip install --upgrade pip || {
    echo "❌ Failed to upgrade pip"
    exit 1
}

python3 -m pip install -r requirements.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}

# Install the package in development mode
echo "📦 Installing findr in development mode..."
python3 -m pip install -e . || {
    echo "❌ Failed to install findr"
    exit 1
}

# Create findr command
FINDR_COMMAND="#!/bin/bash
cd \"$SCRIPT_DIR\"
source \"$SCRIPT_DIR/venv/bin/activate\"
python3 -m findr.cli \"\$@\"
deactivate"

# Create the .local/bin directory if it doesn't exist
mkdir -p "$HOME/.local/bin"

# Create the findr executable
echo "$FINDR_COMMAND" > "$HOME/.local/bin/findr"
chmod +x "$HOME/.local/bin/findr"

# Add ~/.local/bin to PATH if not already present
if ! grep -q "export PATH=\"\$HOME/.local/bin:\$PATH\"" "$SHELL_CONFIG"; then
    echo -e "\n# Add ~/.local/bin to PATH for findr" >> "$SHELL_CONFIG"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
fi

echo -e "\n✨ Installation Complete!"
echo "Please run: source $SHELL_CONFIG"
echo "Then type 'findr' to start searching!"
