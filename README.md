# Communications MCP Server

A comprehensive Model Context Protocol (MCP) server that provides email, Telegram, and Signal communication tools for Claude Code. Built with FastMCP for reliable, type-safe communication workflows.

## Features

- **📧 Email** - One-way communication via Resend API
- **📱 Telegram** - Bidirectional messaging with bot integration  
- **💬 Signal** - Bidirectional messaging via signal-cli wrapper
- **⚙️ Auto-configuration** - Smart setup with environment detection
- **🔒 Type Safety** - Full type hints and validation
- **⏱️ Timeout Handling** - Configurable timeouts (default: 3 minutes)

## Installation

### Method 1: Install from GitHub (Recommended)
```bash
pip install git+https://github.com/luxiaolei/comm-mcps.git
```

### Method 2: Install from PyPI
```bash
pip install comm-mcps
```

### Method 3: Development Setup
```bash
git clone https://github.com/luxiaolei/comm-mcps.git
cd comm-mcps
./setup.sh
```

## Quick Start

1. **Create environment configuration:**
   ```bash
   # Create .env file with your credentials
   cat > .env << EOF
   # Email (Resend)
   RESEND_API_KEY=your_resend_api_key
   FROM_EMAIL=noreply@resend.dev
   
   # Telegram
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_CHAT_ID=your_chat_id
   
   # Signal
   SIGNAL_PHONE_NUMBER=+1234567890
   SIGNAL_CLI_PATH=signal-cli
   EOF
   ```

2. **Use as CLI:**
   ```bash
   # Check status
   comm-mcps-cli status
   
   # Send email
   comm-mcps-cli email "Alert" "Your message"
   
   # Send Telegram (bidirectional)
   comm-mcps-cli telegram "Hello" --reply --timeout 60
   
   # Send Signal (bidirectional)
   comm-mcps-cli signal "Hello" "+1234567890" --reply
   ```

3. **Use as Python library:**
   ```python
   import asyncio
   from comm_mcps.tools.email import send_email
   
   # Send notification
   result = asyncio.run(send_email("user@example.com", "Alert", "Message"))
   ```

4. **Use with Claude Code MCP:**
   Copy `.mcp.json` to your project and the tools will be available in Claude Code.

## Available Tools

### Email Tool

#### `email_tool`
Send emails via Resend API (one-way notifications only).

**Features:**
- Uses `noreply@resend.dev` as sender (hardcoded)
- Configurable default recipient via environment
- Returns simple status: "Email sent to {recipient}" or "Email failed: {error}"

```json
{
  "tool": "email_tool",
  "args": {
    "subject": "Trading Alert",
    "body": "Your notification message",
    "to": "recipient@example.com",
    "html_body": "<h1>Optional HTML</h1>"
  }
}
```

### Telegram Tool

#### `telegram_tool`
Unified bidirectional Telegram messaging with 1-second polling.

**Features:**
- Uses `TELEGRAM_CHAT_ID` from environment (not argument)
- Send messages and optionally wait for replies
- 1-second polling when `expected_reply=True`
- Configure your own Telegram bot

```json
{
  "tool": "telegram_tool",
  "args": {
    "message": "Hello from Claude!",
    "expected_reply": true,
    "timeout": 180.0
  }
}
```

### Signal Tool

#### `signal_tool`
Unified bidirectional Signal messaging with 1-second polling.

**Features:**
- Send to any phone number or group ID
- Wait for replies with 1-second polling
- Uses your configured phone number as sender
- Secure end-to-end encryption

```json
{
  "tool": "signal_tool",
  "args": {
    "message": "Hello via Signal!",
    "recipient": "+1234567890",
    "expected_reply": true,
    "timeout": 180.0
  }
}
```

### Status Tool

#### `get_communication_status`
Get configuration status for all services.

```json
{
  "tool": "get_communication_status",
  "args": {}
}
```

## Service Setup

### Email (Resend)

1. Sign up at [resend.com](https://resend.com)
2. Get your API key from the dashboard
3. Add domain and verify sender email
4. Set `RESEND_API_KEY` and `FROM_EMAIL` in `.env`

### Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get bot token from BotFather
3. Get API credentials from [my.telegram.org](https://my.telegram.org)
4. Set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, and `TELEGRAM_API_HASH` in `.env`

### Signal

1. Install signal-cli (automated by setup.sh)
2. Register your phone number: `signal-cli -u +1234567890 register`
3. Verify with SMS code: `signal-cli -u +1234567890 verify CODE`
4. Set `SIGNAL_PHONE_NUMBER` in `.env`

## Development

### Project Structure

```
comm_mcps/
├── src/comm_mcps/
│   ├── server.py          # Main FastMCP server
│   ├── config.py          # Configuration management
│   └── tools/
│       ├── email.py       # Email tool implementation
│       ├── telegram.py    # Telegram tools
│       └── signal.py      # Signal tools
├── setup.sh               # Setup script
└── pyproject.toml         # Project configuration
```

### Running Locally

```bash
# Install dependencies
uv sync

# Run server
uv run python -m comm_mcps.server

# Test tools
uv run python -c "from comm_mcps.tools.email import get_email_status; print(get_email_status())"
```

### Configuration Options

All tools support these standard parameters:

- `expected_reply: bool = False` - Whether to expect a response
- `timeout: float = 180.0` - Operation timeout in seconds (3 minutes default)

Environment variables:

- `MCP_TRANSPORT` - Transport protocol (stdio, http, sse)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Error Handling

The server provides structured error responses:

```json
{
  "status": "error",
  "error": "Descriptive error message"
}
```

Common error scenarios:
- Missing configuration (API keys, credentials)
- Network timeouts
- Service-specific errors (invalid recipients, rate limits)
- CLI tool unavailability (signal-cli)

## Troubleshooting

### Email Issues
- Verify Resend API key and sender domain
- Check sender email is verified in Resend dashboard
- Ensure recipient email format is valid

### Telegram Issues  
- Verify bot token with BotFather
- Check API ID/hash from my.telegram.org
- Ensure bot is added to target chats/groups

### Signal Issues
- Verify signal-cli installation: `signal-cli --version`
- Check phone number registration: `signal-cli -u +phone listIdentities`
- Ensure signal-cli binary is in PATH

### General Issues
- Check `.env` file exists and has correct values
- Verify Python 3.10+ installation
- Run setup.sh to reinstall dependencies

## License

MIT License - see LICENSE file for details.