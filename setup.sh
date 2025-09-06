#!/bin/bash

set -e

echo "🚀 Communications MCP Setup Script"
echo "=================================="
echo ""

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "src/comm_mcps" ]; then
    log_error "Please run this script from the comm_mcps project root directory"
    exit 1
fi

log_info "Setting up Communications MCP..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi

log_success "Python version: $PYTHON_VERSION"

# Check for uv and install if not present
if ! command -v uv &> /dev/null; then
    log_warning "uv package manager not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    log_success "uv installed"
else
    log_success "uv package manager found"
fi

# Initialize project with uv if not already initialized
if [ ! -f "uv.lock" ]; then
    log_info "Initializing project with uv..."
    uv sync
    log_success "Project initialized"
else
    log_info "Installing/updating dependencies..."
    uv sync
    log_success "Dependencies updated"
fi

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating .env file from template..."
    cp .env.example .env
    log_warning "Please edit .env file with your API credentials"
else
    log_info ".env file already exists"
fi

# Check for signal-cli installation
log_info "Checking Signal CLI installation..."
if command -v signal-cli &> /dev/null; then
    SIGNAL_VERSION=$(signal-cli --version 2>&1 || echo "unknown")
    log_success "signal-cli found: $SIGNAL_VERSION"
else
    log_warning "signal-cli not found. Installing..."
    
    # Detect OS and install signal-cli
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install signal-cli
            log_success "signal-cli installed via Homebrew"
        else
            log_error "Homebrew not found. Please install signal-cli manually: https://github.com/AsamK/signal-cli"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        log_info "Installing signal-cli on Linux..."
        
        # Download latest release
        SIGNAL_CLI_VERSION=$(curl -s https://api.github.com/repos/AsamK/signal-cli/releases/latest | grep -o '"tag_name": "v[^"]*' | grep -o 'v[^"]*')
        SIGNAL_CLI_URL="https://github.com/AsamK/signal-cli/releases/download/${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION#v}.tar.gz"
        
        # Create local bin directory if it doesn't exist
        mkdir -p ~/.local/bin
        
        # Download and extract
        cd /tmp
        curl -L -o signal-cli.tar.gz "$SIGNAL_CLI_URL"
        tar xf signal-cli.tar.gz
        mv signal-cli-* ~/.local/signal-cli
        ln -sf ~/.local/signal-cli/bin/signal-cli ~/.local/bin/signal-cli
        
        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            export PATH="$HOME/.local/bin:$PATH"
        fi
        
        cd - > /dev/null
        log_success "signal-cli installed to ~/.local/bin/signal-cli"
    else
        log_warning "Unsupported OS. Please install signal-cli manually: https://github.com/AsamK/signal-cli"
    fi
fi

# Test the installation
log_info "Testing MCP server..."
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Check if we can import the module
if uv run python3 -c "from comm_mcps.server import mcp; print('✅ MCP server can be imported')" 2>/dev/null; then
    log_success "MCP server installation verified"
else
    log_error "MCP server import failed. Check your Python environment."
    exit 1
fi

# Generate Claude Code MCP configuration
log_info "Generating Claude Code MCP configuration..."

# Get absolute path to the project
PROJECT_PATH=$(pwd)
PYTHON_PATH=$(uv run which python3)

# Create the MCP configuration JSON
cat > claude_mcp_config.json << EOF
{
  "mcpServers": {
    "communications": {
      "command": "$PYTHON_PATH",
      "args": ["-m", "comm_mcps.server"],
      "cwd": "$PROJECT_PATH",
      "env": {
        "PYTHONPATH": "$PROJECT_PATH/src"
      }
    }
  }
}
EOF

log_success "Claude Code MCP configuration created: claude_mcp_config.json"

# Display setup completion and detailed configuration guides
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""

# Check current service configurations
echo "📋 Current Service Configuration Status:"
if uv run python3 -c "
from comm_mcps.config import config
import os
os.chdir('$PROJECT_PATH')
email_configured = config.is_email_configured()
telegram_configured = config.is_telegram_configured()
signal_configured = config.is_signal_configured()
print(f'📧 Email: {\"✅ Configured\" if email_configured else \"❌ Not configured\"}')
print(f'📱 Telegram: {\"✅ Configured\" if telegram_configured else \"❌ Not configured\"}')  
print(f'💬 Signal: {\"✅ Configured\" if signal_configured else \"❌ Not configured\"}')
exit(0 if (email_configured or telegram_configured or signal_configured) else 1)
" 2>/dev/null; then
    SERVICES_CONFIGURED=true
else
    SERVICES_CONFIGURED=false
    log_warning "No services configured yet. Please follow the setup guides below."
fi

echo ""
echo "📚 DETAILED SERVICE SETUP GUIDES"
echo "=================================="

# Email Setup Guide
echo ""
echo "📧 EMAIL SETUP (Resend API)"
echo "----------------------------"
echo ""
echo "Step 1: Create Resend Account"
log_info "   1. Go to https://resend.com"
log_info "   2. Click 'Sign Up' and create an account"
log_info "   3. Verify your email address"
echo ""
echo "Step 2: Add and Verify Domain"
log_info "   1. In Resend dashboard, go to 'Domains'"
log_info "   2. Click 'Add Domain'"
log_info "   3. Enter your domain (e.g., yourdomain.com)"
log_info "   4. Add the provided DNS records to your domain"
log_info "   5. Wait for verification (can take up to 24 hours)"
echo ""
echo "Step 3: Get API Key"
log_info "   1. Go to 'API Keys' in the dashboard"
log_info "   2. Click 'Create API Key'"
log_info "   3. Give it a name (e.g., 'Claude MCP')"
log_info "   4. Select 'Sending access' permission"
log_info "   5. Copy the generated API key"
echo ""
echo "Step 4: Configure .env"
log_info "   Add these lines to your .env file:"
echo "   RESEND_API_KEY=re_your_api_key_here"
echo "   FROM_EMAIL=your-email@yourdomain.com"
echo ""
log_warning "Note: FROM_EMAIL must be from a verified domain in Resend"

# Telegram Setup Guide  
echo ""
echo "📱 TELEGRAM SETUP (Bot Integration)"
echo "------------------------------------"
echo ""
echo "Step 1: Create Telegram Bot"
log_info "   1. Open Telegram and search for @BotFather"
log_info "   2. Start a chat with BotFather"
log_info "   3. Send /newbot command"
log_info "   4. Choose a name for your bot (e.g., 'My Claude Bot')"
log_info "   5. Choose a username ending in 'bot' (e.g., 'myclaudebot')"
log_info "   6. Copy the bot token (format: 123456789:ABC-DEF...)"
echo ""
echo "Step 2: Get API Credentials"
log_info "   1. Go to https://my.telegram.org"
log_info "   2. Log in with your phone number"
log_info "   3. Go to 'API development tools'"
log_info "   4. Create a new application:"
log_info "      - App title: 'Claude MCP'"
log_info "      - Short name: 'claude-mcp'"
log_info "      - Platform: 'Other'"
log_info "   5. Copy the 'App api_id' (numeric)"
log_info "   6. Copy the 'App api_hash' (alphanumeric)"
echo ""
echo "Step 3: Configure .env"
log_info "   Add these lines to your .env file:"
echo "   TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
echo "   TELEGRAM_API_ID=12345678"
echo "   TELEGRAM_API_HASH=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
echo ""
echo "Step 4: Test Bot"
log_info "   1. Find your bot on Telegram (search for the username)"
log_info "   2. Send /start to activate it"
log_info "   3. Note: Use bot username (e.g., @myclaudebot) or numeric chat ID in tools"

# Signal Setup Guide
echo ""
echo "💬 SIGNAL SETUP (CLI Integration)"
echo "---------------------------------"
echo ""
echo "Step 1: Install signal-cli (Already Done)"
if command -v signal-cli &> /dev/null; then
    log_success "   ✅ signal-cli is installed and ready"
else
    log_error "   ❌ signal-cli installation failed. Please install manually:"
    log_info "      macOS: brew install signal-cli"
    log_info "      Linux: https://github.com/AsamK/signal-cli#installation"
fi
echo ""
echo "Step 2: Register Phone Number"
log_info "   1. Replace +1234567890 with your actual phone number"
log_info "   2. Run: signal-cli -u +1234567890 register"
log_info "   3. You'll receive an SMS with a verification code"
log_info "   4. Run: signal-cli -u +1234567890 verify CODE"
log_info "      (replace CODE with the 6-digit code from SMS)"
echo ""
echo "Step 3: Test Registration"
log_info "   Run: signal-cli -u +1234567890 listIdentities"
log_info "   If successful, you'll see your phone number listed"
echo ""
echo "Step 4: Configure .env"
log_info "   Add this line to your .env file:"
echo "   SIGNAL_PHONE_NUMBER=+1234567890"
echo ""
log_warning "Note: Use international format (+country_code_number)"

# Claude Code Integration Guide
echo ""
echo "🤖 CLAUDE CODE INTEGRATION"
echo "============================="
echo ""
echo "Step 1: Locate MCP Settings"
log_info "   1. Open Claude Code (claude.ai/code)"
log_info "   2. Click the settings icon (⚙️) in the top right"
log_info "   3. Look for 'MCP Servers' or 'Model Context Protocol' section"
echo ""
echo "Step 2: Add Configuration"
log_info "   1. Copy the contents of: claude_mcp_config.json"
log_info "   2. Paste into the MCP servers configuration"
log_info "   3. Save the settings"
echo ""
echo "Step 3: Verify Integration"
log_info "   1. Look for 'Communications MCP' in available tools"
log_info "   2. You should see tools like send_email_tool, send_telegram_tool"
echo ""
log_info "Generated MCP config file: $(pwd)/claude_mcp_config.json"

# Testing Guide
echo ""
echo "🧪 TESTING YOUR SETUP"
echo "======================"
echo ""
echo "Test 1: Check Service Status"
log_info "   Run: uv run python3 -c \"from comm_mcps.server import mcp; import asyncio; from comm_mcps.tools.email import get_email_status; print(asyncio.run(get_email_status()))\""
echo ""
echo "Test 2: Run MCP Server"
log_info "   Run: uv run python3 -m comm_mcps.server"
log_info "   Server should start without errors"
log_info "   Press Ctrl+C to stop"
echo ""
echo "Test 3: Example Tool Calls (in Claude Code)"
echo ""
echo "📧 Email Test:"
echo '   {"tool": "send_email_tool", "args": {"to": "test@example.com", "subject": "Test", "body": "Hello from Claude!"}}'
echo ""
echo "📱 Telegram Test:"
echo '   {"tool": "send_telegram_tool", "args": {"message": "Hello!", "chat_id": "@your_bot_username"}}'
echo ""  
echo "💬 Signal Test:"
echo '   {"tool": "send_signal_tool", "args": {"message": "Hello!", "recipient": "+1234567890"}}'
echo ""
echo "📋 Status Check:"
echo '   {"tool": "get_communication_status", "args": {}}'

# Final Instructions
echo ""
echo "⚡ QUICK START CHECKLIST"
echo "========================"
echo ""
log_info "□ 1. Edit .env file with your API credentials"
log_info "□ 2. For Signal: Run registration commands above"
log_info "□ 3. Copy claude_mcp_config.json to Claude Code MCP settings"
log_info "□ 4. Test with: uv run python3 -m comm_mcps.server"
log_info "□ 5. Try the example tool calls in Claude Code"
echo ""

if [ "$SERVICES_CONFIGURED" = true ]; then
    log_success "🎉 At least one service is configured! You can start using the MCP tools."
else
    log_warning "⚠️  Please configure at least one service in .env before using the tools."
fi

echo ""
echo "📞 Need Help?"
echo "=============="
log_info "• Check README.md for detailed documentation"
log_info "• Review .env.example for configuration format"
log_info "• Run './setup.sh' again if you encounter issues"
log_info "• Check logs when running the server for error details"
echo ""

log_success "Communications MCP setup complete! 🚀"

exit 0