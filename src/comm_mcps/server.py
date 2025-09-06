"""Main FastMCP server for communications tools."""

import asyncio
import logging
from typing import Dict

from fastmcp import FastMCP

from .config import config
from .tools.email import send_email, get_email_status
from .tools.telegram_unified import (
    telegram_send_with_reply,
    get_telegram_unified_status
)
from .tools.signal_unified import (
    signal_send_with_reply,
    get_signal_unified_status
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("Communications MCP Server")


@mcp.tool()
async def email_tool(
    subject: str,
    body: str,
    to: str = "26442779@qq.com",
    html_body: str = None
) -> str:
    """Send an email notification using Resend API.
    
    Uses noreply@resend.dev as sender for all emails (perfect for notifications).
    
    Args:
        subject: Email subject line
        body: Plain text email content
        to: Recipient email address (default: 26442779@qq.com)
        html_body: Optional HTML version of the email
    
    Returns:
        Simple status message: "Email sent to {recipient}" or "Email failed: {error}"
    """
    result = await send_email(to, subject, body, False, 30.0, None, html_body)
    
    if result.get("status") == "sent":
        return f"Email sent to {to}"
    else:
        error = result.get("error", "Unknown error")
        return f"Email failed: {error}"


@mcp.tool()
async def telegram_tool(
    message: str,
    expected_reply: bool = False,
    timeout: float = 180.0
) -> Dict:
    """Send a Telegram message and optionally wait for reply.
    
    This unified tool sends a message to the configured chat (TELEGRAM_CHAT_ID)
    and can wait for a reply with 1-second polling if expected_reply=True.
    
    Args:
        message: Message content to send
        expected_reply: Whether to wait for a reply (default False)
        timeout: How long to wait for reply in seconds (default 3 minutes)
    
    Returns:
        Dict with send status and reply if expected_reply=True
    """
    return await telegram_send_with_reply(message, expected_reply, timeout)


@mcp.tool()
async def signal_tool(
    message: str,
    recipient: str,
    expected_reply: bool = False,
    timeout: float = 180.0
) -> Dict:
    """Send a Signal message and optionally wait for reply.
    
    This unified tool sends a message and can wait for a reply with 1-second polling
    if expected_reply=True. Works exactly like telegram_tool but for Signal.
    
    Args:
        message: Message content to send
        recipient: Target phone number (e.g., +1234567890) or group ID
        expected_reply: Whether to wait for a reply (default False)
        timeout: How long to wait for reply in seconds (default 3 minutes)
    
    Returns:
        Dict with send status and reply if expected_reply=True
    """
    return await signal_send_with_reply(message, recipient, expected_reply, timeout)


@mcp.tool()
async def get_communication_status() -> Dict:
    """Get status of all communication services.
    
    Returns:
        Dict with status information for all services
    """
    email_status = await get_email_status()
    telegram_status = await get_telegram_unified_status()
    signal_status = await get_signal_unified_status()
    
    return {
        "email": email_status,
        "telegram": telegram_status,
        "signal": signal_status,
        "server": {
            "name": "Communications MCP Server",
            "version": "0.1.0",
            "transport": config.mcp_transport,
            "log_level": config.log_level
        }
    }


async def cleanup():
    """Cleanup resources on server shutdown."""
    logger.info("Shutting down Communications MCP Server...")
    
    # No specific cleanup needed for unified tools
    logger.info("Cleanup completed.")


def main():
    """Main entry point for the server."""
    logger.info("Starting Communications MCP Server...")
    logger.info(f"Transport: {config.mcp_transport}")
    logger.info(f"Email configured: {config.is_email_configured()}")
    logger.info(f"Telegram configured: {config.is_telegram_configured()}")
    logger.info(f"Signal configured: {config.is_signal_configured()}")
    
    try:
        # Run the server
        mcp.run(transport=config.mcp_transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
    finally:
        # Cleanup on exit
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()