# Communications MCP Server

A comprehensive Model Context Protocol (MCP) server that provides email, Telegram, and Signal communication tools for Claude Code. Built with FastMCP for reliable, type-safe communication workflows.

## Features

- **📧 Email** - One-way communication via Resend API
- **📱 Telegram** - Bidirectional messaging with bot integration  
- **💬 Signal** - Bidirectional messaging via signal-cli wrapper
- **⚙️ Auto-configuration** - Smart setup with environment detection
- **🔒 Type Safety** - Full type hints and validation
- **⏱️ Timeout Handling** - Configurable timeouts (default: 3 minutes)

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd comm_mcps
   ./setup.sh
   ```

2. **Configure services in `.env`:**
   ```bash
   # Email (Resend)
   RESEND_API_KEY=your_resend_api_key
   FROM_EMAIL=your-email@domain.com
   
   # Telegram
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   
   # Signal
   SIGNAL_PHONE_NUMBER=+1234567890
   ```

3. **Add to Claude Code:**
   Copy `claude_mcp_config.json` contents to your Claude Code MCP settings.

## Available Tools

### Email Tool

#### `email_tool`
Send emails via Resend API (one-way notifications only).

**Features:**
- Uses `noreply@resend.dev` as sender (hardcoded)
- Default recipient: `26442779@qq.com`
- Returns simple status: "Email sent to {recipient}" or "Email failed: {error}"

```json
{
  "tool": "email_tool",
  "args": {
    "subject": "Trading Alert",
    "body": "Your notification message",
    "to": "26442779@qq.com",
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
- Bot: @cctrading01_bot

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
- Uses `+85257833828` as sender (from environment)
- Secure end-to-end encryption

```json
{
  "tool": "signal_tool",
  "args": {
    "message": "Hello via Signal!",
    "recipient": "+8618611342177",
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