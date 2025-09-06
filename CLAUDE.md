# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Think carefully and implement the most concise solution that changes as little code as possible.

## Project Architecture

This is a **Communications MCP Server** built with FastMCP that provides email, Telegram, and Signal messaging tools for Claude Code integration.

### Core Components

**MCP Server** (`src/comm_mcps/server.py`):
- FastMCP-based server with 4 unified communication tools
- STDIO transport for Claude Code integration
- Async/await architecture for concurrent operations

**Configuration System** (`src/comm_mcps/config.py`):
- Pydantic-based configuration with `.env` file support
- Service validation and credential management
- Environment variable precedence

**Communication Tools** (`src/comm_mcps/tools/`):
- **email.py**: Resend API integration (one-way notifications)
- **telegram_unified.py**: Telegram Bot API with polling (bidirectional)
- **signal_unified.py**: signal-cli wrapper with polling (bidirectional)

## Development Commands

**Install and Setup**:
```bash
# Initial setup (installs dependencies, creates config)
./setup.sh

# Manual dependency installation
uv sync

# Run MCP server
uv run python3 -m comm_mcps.server
```

**Testing Communication Tools**:
```bash
# Test individual services
uv run python3 -c "
from src.comm_mcps.tools.email import get_email_status
import asyncio; print(asyncio.run(get_email_status()))
"

# Test server tools directly
uv run python3 -c "
from src.comm_mcps.tools.telegram_unified import telegram_send_with_reply
import asyncio; print(asyncio.run(telegram_send_with_reply('test', False)))
"

# Test Signal functionality
uv run python3 -c "
from src.comm_mcps.tools.signal_unified import signal_send_with_reply
import asyncio; print(asyncio.run(signal_send_with_reply('test', '+1234567890', False)))
"
```

**Configuration Management**:
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Test configuration status
uv run python3 -c "
from src.comm_mcps.config import config
print(f'Email: {config.is_email_configured()}')
print(f'Telegram: {config.is_telegram_configured()}')
print(f'Signal: {config.is_signal_configured()}')
"
```

## MCP Integration

**Add to Claude Code Projects**:
```bash
# Copy MCP configuration to any project
cp .mcp.json /path/to/your/project/

# Use with Claude Code
cd /path/to/your/project
claude  # Communications tools will be available
```

**MCP Configuration** (`.mcp.json`):
- Uses `uv run python3 -m comm_mcps.server` as command
- Sets `PYTHONPATH` to include source directory
- Project-scoped for easy integration

## Service Configuration

**Email (Resend API)**:
- API Key: Set `RESEND_API_KEY` in `.env`
- Sender: Hardcoded to `noreply@resend.dev`
- Default recipient: Configure in environment

**Telegram (Bot API)**:
- Bot Token: `TELEGRAM_BOT_TOKEN` 
- API Credentials: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`
- Chat ID: `TELEGRAM_CHAT_ID` (configure your target chat)
- Create your own bot via @BotFather

**Signal (CLI Wrapper)**:
- Phone Number: `SIGNAL_PHONE_NUMBER` (your registered number)
- CLI Path: `SIGNAL_CLI_PATH=signal-cli`
- Requires Java runtime and signal-cli installation

## Tool Signatures

All tools follow unified patterns with `expected_reply` and `timeout` parameters:

**Email Tool** (One-way):
```python
email_tool(subject: str, body: str, to: str = "default@example.com") -> str
```

**Telegram Tool** (Bidirectional):
```python
telegram_tool(message: str, expected_reply: bool = False, timeout: float = 180.0) -> Dict
```

**Signal Tool** (Bidirectional):
```python
signal_tool(message: str, recipient: str, expected_reply: bool = False, timeout: float = 180.0) -> Dict
```

## Bidirectional Communication

**Telegram and Signal** support bidirectional communication:
- `expected_reply=False`: Send message and return immediately
- `expected_reply=True`: Send message then poll for replies at 1-second intervals
- **Polling Logic**: Continues until reply received or timeout reached
- **Response Handling**: Structured responses with wait times and message content

## Error Handling

**Service-specific error handling**:
- Configuration validation before operations
- API timeout handling (30s for individual calls)
- Structured error responses with clear messages
- Graceful degradation when services unavailable

## Dependencies

**Runtime**:
- Python 3.10+
- FastMCP 2.0+
- uv package manager

**External Services**:
- Java Runtime (for signal-cli)
- signal-cli binary
- Internet connectivity for APIs

**Development**:
- pytest for testing
- ruff for linting
- pre-commit for code quality

## Architecture Patterns

**Unified Tools**: Each communication method has one primary tool that handles both sending and optional reply waiting.

**Configuration Hierarchy**: CLI args → Environment variables → Defaults

**Transport Agnostic**: Uses FastMCP's transport abstraction (STDIO/HTTP/SSE)

**Error Resilience**: Individual service failures don't affect other services

## ABSOLUTE RULES:

- NO PARTIAL IMPLEMENTATION
- NO SIMPLIFICATION : no "//This is simplified stuff for now, complete implementation would blablabla"
- NO CODE DUPLICATION : check existing codebase to reuse functions and constants Read files before writing new functions. Use common sense function name to find them easily.
- NO DEAD CODE : either use or delete from codebase completely
- IMPLEMENT TEST FOR EVERY FUNCTIONS
- NO CHEATER TESTS : test must be accurate, reflect real usage and be designed to reveal flaws. No useless tests! Design tests to be verbose so we can use them for debuging.
- NO INCONSISTENT NAMING - read existing codebase naming patterns.
- NO OVER-ENGINEERING - Don't add unnecessary abstractions, factory patterns, or middleware when simple functions would work. Don't think "enterprise" when you need "working"
- NO MIXED CONCERNS - Don't put validation logic inside API handlers, database queries inside UI components, etc. instead of proper separation
- NO RESOURCE LEAKS - Don't forget to close database connections, clear timeouts, remove event listeners, or clean up file handles

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.