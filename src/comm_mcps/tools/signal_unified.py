"""Unified Signal tool with send-and-wait functionality."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .signal import send_signal_message, receive_signal_messages
from ..config import config

logger = logging.getLogger(__name__)


async def signal_send_with_reply(
    message: str,
    recipient: str,
    expected_reply: bool = False,
    timeout: float = 180.0
) -> Dict[str, Any]:
    """Send a Signal message and optionally wait for reply.
    
    This is the unified tool that handles both sending and receiving.
    Similar to telegram_tool but for Signal.
    
    Args:
        message: Message content to send
        recipient: Target phone number (e.g., +1234567890) or group ID
        expected_reply: Whether to wait for a reply (default False)
        timeout: How long to wait for reply in seconds (default 3 minutes)
    
    Returns:
        Dict with send status and reply if expected_reply=True
    """
    if not config.is_signal_configured():
        return {
            "status": "error",
            "error": "Signal not configured. Set SIGNAL_PHONE_NUMBER in .env"
        }
    
    # Step 1: Send the message
    logger.info(f"Sending Signal message to {recipient}: {message[:50]}...")
    send_result = await send_signal_message(message, recipient, expected_reply, 30.0)
    
    if send_result.get("status") != "sent":
        return {
            "status": "send_failed",
            "error": send_result.get("error", "Unknown send error")
        }
    
    response = {
        "status": "sent",
        "message_sent": {
            "recipient": recipient,
            "message": message,
            "expected_reply": expected_reply
        }
    }
    
    # Step 2: Wait for reply if expected
    if expected_reply:
        logger.info(f"Waiting for Signal reply (timeout: {timeout}s)...")
        
        reply_result = await wait_for_signal_reply(
            recipient=recipient,
            timeout=timeout
        )
        
        response["reply"] = reply_result
        
        if reply_result.get("status") == "reply_received":
            response["status"] = "completed_with_reply"
            logger.info(f"Signal reply received after {reply_result['wait_time_seconds']:.1f}s")
        elif reply_result.get("status") == "timeout":
            response["status"] = "sent_but_no_reply"
            logger.warning(f"No Signal reply received within {timeout}s")
        else:
            response["status"] = "sent_but_error_waiting"
    
    return response


async def wait_for_signal_reply(
    recipient: str,
    timeout: float = 180.0
) -> Dict[str, Any]:
    """Wait for a Signal reply with 1-second polling.
    
    Args:
        recipient: Phone number or group ID we sent message to
        timeout: Maximum wait time in seconds
        
    Returns:
        Dict with reply information or timeout
    """
    start_time = datetime.now()
    timeout_delta = timedelta(seconds=timeout)
    
    logger.info(f"Waiting for Signal reply from {recipient} (timeout: {timeout}s)")
    
    while (datetime.now() - start_time) < timeout_delta:
        try:
            # Poll for new Signal messages every 1 second
            receive_result = await receive_signal_messages(timeout=1.0)
            
            if receive_result.get("status") == "success" and receive_result.get("messages"):
                messages = receive_result.get("messages", [])
                
                for msg in messages:
                    sender = msg.get("sender")
                    message_content = msg.get("message", "")
                    
                    # Check if this message is from our target recipient
                    # (In Signal, replies come from the same number we sent to)
                    if sender == recipient and message_content:
                        return {
                            "status": "reply_received",
                            "message": {
                                "text": message_content,
                                "sender": sender,
                                "timestamp": msg.get("timestamp"),
                                "group_name": msg.get("group_name")
                            },
                            "wait_time_seconds": (datetime.now() - start_time).total_seconds()
                        }
            
            # Wait 1 second before next poll
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.exception(f"Error during Signal reply polling: {e}")
            await asyncio.sleep(1)
    
    # Timeout reached
    return {
        "status": "timeout",
        "message": "No Signal reply received within timeout period",
        "waited_seconds": timeout
    }


async def get_signal_unified_status() -> Dict[str, Any]:
    """Get status of unified Signal configuration.
    
    Returns:
        Dict with configuration and status information
    """
    return {
        "service": "signal_unified",
        "configured": config.is_signal_configured(),
        "phone_number": config.signal_phone_number if config.is_signal_configured() else None,
        "cli_path": config.signal_cli_path,
        "capabilities": [
            "Send messages to any phone number or group",
            "Wait for replies with 1-second polling",
            "Configurable timeout (default 3 minutes)",
            "Uses environment SIGNAL_PHONE_NUMBER"
        ]
    }