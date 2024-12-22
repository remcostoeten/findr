#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print styled messages
print_step() { echo -e "\n${BLUE}$1${NC}"; }
print_success() { echo -e "${GREEN}$1${NC}"; }
print_error() { echo -e "${RED}$1${NC}"; exit 1; }
print_warning() { echo -e "${YELLOW}$1${NC}"; }

clear
cat << "EOF"
 _____ _           _      
|  ___(_)_ __   __| |_ __ 
| |_  | | '_ \ / _` | '__|
|  _| | | | | | (_| | |   
|_|   |_|_| |_|\__,_|_|   
EOF
print_step "🔍 Interactive File Search Tool"
echo -e "Version: 0.1.0\n"

# Check Python
command -v python3 &> /dev/null || print_error "❌ Python 3 is required but not installed"

# Function to detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "mac" ;;
        Linux*)     echo "linux" ;;
        *)         echo "unknown" ;;
    esac
}

# Function to detect current shell and config file
detect_shell() {
    # Check if we're running in zsh
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/usr/bin/zsh" ] || [ "$SHELL" = "/bin/zsh" ]; then
        echo "zsh"
    # Check if we're running in bash
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/usr/bin/bash" ] || [ "$SHELL" = "/bin/bash" ]; then
        echo "bash"
    else
        echo "unknown"
    fi
}

get_shell_config() {
    local shell_type=$1
    local os_type=$2
    
    case $shell_type in
        "zsh")
            if [ -f "$HOME/.zshrc" ]; then
                echo "$HOME/.zshrc"
            else
                echo "$HOME/.zprofile"
            fi
            ;;
        "bash")
            if [ "$os_type" = "mac" ]; then
                if [ -f "$HOME/.bash_profile" ]; then
                    echo "$HOME/.bash_profile"
                elif [ -f "$HOME/.profile" ]; then
                    echo "$HOME/.profile"
                else
                    echo "$HOME/.bash_profile"
                fi
            else
                if [ -f "$HOME/.bashrc" ]; then
                    echo "$HOME/.bashrc"
                else
                    echo "$HOME/.bash_profile"
                fi
            fi
            ;;
        *)
            if [ "$os_type" = "mac" ]; then
                echo "$HOME/.profile"
            else
                echo "$HOME/.bashrc"
            fi
            ;;
    esac
}

# Detect OS and current shell
OS_TYPE=$(detect_os)
CURRENT_SHELL=$(detect_shell)
print_step "🖥️  System Detection"
echo -e "Detected OS: ${YELLOW}$OS_TYPE${NC}"
echo -e "Detected shell: ${YELLOW}$CURRENT_SHELL${NC}"

# Interactive shell selection
echo -e "\nSelect your shell configuration:"
echo -e "${YELLOW}1${NC}) Zsh  (~/.zshrc)"
if [ "$OS_TYPE" = "mac" ]; then
    echo -e "${YELLOW}2${NC}) Bash (~/.bash_profile)"
else
    echo -e "${YELLOW}2${NC}) Bash (~/.bashrc)"
fi
echo -e "${YELLOW}3${NC}) I don't know (auto-detect)"
read -p "Enter choice [1]: " shell_choice

case ${shell_choice:-1} in
    1) 
        SHELL_TYPE="zsh"
        SHELL_CONFIG="$HOME/.zshrc"
        ;;
    2) 
        SHELL_TYPE="bash"
        if [ "$OS_TYPE" = "mac" ]; then
            SHELL_CONFIG="$HOME/.bash_profile"
        else
            SHELL_CONFIG="$HOME/.bashrc"
        fi
        ;;
    *)  
        SHELL_TYPE=$CURRENT_SHELL
        SHELL_CONFIG=$(get_shell_config "$SHELL_TYPE" "$OS_TYPE")
        ;;
esac

# Create config file if it doesn't exist
if [ ! -f "$SHELL_CONFIG" ]; then
    print_warning "Creating new config file: $SHELL_CONFIG"
    touch "$SHELL_CONFIG"
fi

print_success "✓ Using shell config: $SHELL_CONFIG"

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Create virtual environment
if [ ! -d "venv" ]; then
    print_step "📦 Setting up environment..."
    python3 -m venv venv || print_error "❌ Failed to create virtual environment"
fi

# Install dependencies
print_step "📥 Installing dependencies..."
source venv/bin/activate || print_error "❌ Failed to activate virtual environment"
pip install -q --upgrade pip
pip install -q -r requirements.txt || print_error "❌ Failed to install dependencies"

# Create findr executable
print_step "📝 Creating findr command..."
mkdir -p ~/.local/bin
cat > ~/.local/bin/findr << EOF
#!/bin/bash
# Findr - Interactive File Search Tool
cd "$SCRIPT_DIR" # Ensure we're in the right directory
source venv/bin/activate
PYTHONPATH="$SCRIPT_DIR/src" python3 -m findr.cli
deactivate
EOF
chmod +x ~/.local/bin/findr || print_error "❌ Failed to make findr executable"

# Update PATH
print_step "🔧 Updating system configuration..."
# Remove old entries first
sed -i '/# Findr/d' "$SHELL_CONFIG" 2>/dev/null
sed -i '/findr/d' "$SHELL_CONFIG" 2>/dev/null

# Add new PATH entry
cat >> "$SHELL_CONFIG" << EOF

# Findr - Interactive File Search Tool
export PATH="\$HOME/.local/bin:\$PATH"
EOF

# Update current session
export PATH="$HOME/.local/bin:$PATH"

# Success message
print_success "\n✨ Installation complete!"
print_step "🚀 To start using Findr:"
echo -e "1. Run: ${YELLOW}source $SHELL_CONFIG${NC}"
echo -e "2. Type: ${YELLOW}findr${NC} to start searching"

# VS Code specific instructions
[ -n "$VSCODE_PID" ] && print_warning "\nℹ️  VS Code users: You may need to restart VS Code for the PATH changes to take effect"
