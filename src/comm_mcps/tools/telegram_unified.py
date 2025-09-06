"""Unified Telegram tool with send-and-wait functionality."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import httpx

from ..config import config

logger = logging.getLogger(__name__)


class TelegramUnified:
    """Unified Telegram communication with send-and-wait functionality."""
    
    def __init__(self):
        self.base_url = "https://api.telegram.org/bot"
        self.last_update_id = 0
    
    @property
    def bot_url(self) -> str:
        """Get the bot API URL."""
        return f"{self.base_url}{config.telegram_bot_token}"
    
    async def send_message(self, text: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message to Telegram.
        
        Args:
            text: Message text to send
            chat_id: Optional chat ID (uses config default if not provided)
            
        Returns:
            Dict with send result
        """
        target_chat_id = chat_id or config.telegram_chat_id
        
        if not target_chat_id:
            return {"error": "No chat ID configured. Set TELEGRAM_CHAT_ID in .env"}
        
        try:
            url = f"{self.bot_url}/sendMessage"
            data = {
                "chat_id": target_chat_id,
                "text": text
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=10.0)
                result = response.json()
                
                if result.get("ok"):
                    message = result["result"]
                    return {
                        "status": "sent",
                        "message_id": message["message_id"],
                        "chat_id": target_chat_id,
                        "date": datetime.fromtimestamp(message["date"]).isoformat()
                    }
                else:
                    return {"error": result.get("description", "Send failed")}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def get_updates_since(self, offset: int = 0) -> Dict[str, Any]:
        """Get updates since the specified offset.
        
        Args:
            offset: Update ID offset
            
        Returns:
            Dict with updates
        """
        try:
            params = {
                "offset": offset,
                "limit": 100,
                "timeout": 1,  # Short timeout for frequent polling
                "allowed_updates": ["message"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_url}/getUpdates",
                    params=params,
                    timeout=3.0
                )
                
                data = response.json()
                
                if data.get("ok"):
                    updates = data.get("result", [])
                    return {
                        "status": "success",
                        "updates": updates
                    }
                else:
                    return {"error": data.get("description", "Failed to get updates")}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def wait_for_reply(
        self, 
        sent_message_id: int,
        chat_id: str,
        timeout: float = 180.0
    ) -> Dict[str, Any]:
        """Wait for a reply message after sending.
        
        Args:
            sent_message_id: ID of the message we sent
            chat_id: Chat ID to monitor
            timeout: Maximum wait time in seconds
            
        Returns:
            Dict with reply information or timeout
        """
        start_time = datetime.now()
        timeout_delta = timedelta(seconds=timeout)
        
        # Get initial offset
        updates_result = await self.get_updates_since(self.last_update_id)
        if "error" in updates_result:
            return {"error": f"Failed to initialize polling: {updates_result['error']}"}
        
        # Update offset to avoid old messages
        updates = updates_result.get("updates", [])
        if updates:
            self.last_update_id = updates[-1]["update_id"] + 1
        
        logger.info(f"Waiting for reply to message {sent_message_id} (timeout: {timeout}s)")
        
        while (datetime.now() - start_time) < timeout_delta:
            try:
                # Poll for new updates
                updates_result = await self.get_updates_since(self.last_update_id)
                
                if "error" in updates_result:
                    logger.warning(f"Polling error: {updates_result['error']}")
                    await asyncio.sleep(1)
                    continue
                
                updates = updates_result.get("updates", [])
                
                for update in updates:
                    self.last_update_id = update["update_id"] + 1
                    
                    if "message" not in update:
                        continue
                    
                    message = update["message"]
                    
                    # Check if this is from our target chat
                    if str(message["chat"]["id"]) != str(chat_id):
                        continue
                    
                    # Check if this is a reply to our message or just a new message
                    reply_to = message.get("reply_to_message")
                    is_reply = reply_to and reply_to["message_id"] == sent_message_id
                    
                    # Accept any message from the chat after our message
                    message_time = datetime.fromtimestamp(message["date"])
                    
                    return {
                        "status": "reply_received",
                        "message": {
                            "id": message["message_id"],
                            "text": message.get("text", ""),
                            "date": message_time.isoformat(),
                            "is_direct_reply": is_reply,
                            "from": {
                                "id": message["from"]["id"],
                                "username": message["from"].get("username"),
                                "first_name": message["from"].get("first_name"),
                                "last_name": message["from"].get("last_name")
                            }
                        },
                        "wait_time_seconds": (datetime.now() - start_time).total_seconds()
                    }
                
                # Wait 1 second before next poll
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.exception(f"Error during reply polling: {e}")
                await asyncio.sleep(1)
        
        # Timeout reached
        return {
            "status": "timeout",
            "message": "No reply received within timeout period",
            "waited_seconds": timeout
        }


# Global instance
telegram_unified = TelegramUnified()


async def telegram_send_with_reply(
    message: str,
    expected_reply: bool = False,
    timeout: float = 180.0
) -> Dict[str, Any]:
    """Send a Telegram message and optionally wait for reply.
    
    This is the single unified tool that handles both sending and receiving.
    Uses TELEGRAM_CHAT_ID from environment, not as argument.
    
    Args:
        message: Message text to send
        expected_reply: Whether to wait for a reply (default False)
        timeout: How long to wait for reply in seconds (default 3 minutes)
    
    Returns:
        Dict with send status and reply if expected_reply=True
    """
    if not config.is_telegram_configured():
        return {
            "status": "error",
            "error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN, TELEGRAM_API_ID, and TELEGRAM_API_HASH"
        }
    
    if not config.is_telegram_chat_configured():
        return {
            "status": "error", 
            "error": "No default chat ID configured. Set TELEGRAM_CHAT_ID in .env"
        }
    
    # Step 1: Send the message
    logger.info(f"Sending message to chat {config.telegram_chat_id}: {message[:50]}...")
    send_result = await telegram_unified.send_message(message)
    
    if "error" in send_result:
        return {
            "status": "send_failed",
            "error": send_result["error"]
        }
    
    response = {
        "status": "sent",
        "message_sent": {
            "id": send_result["message_id"],
            "text": message,
            "chat_id": send_result["chat_id"],
            "date": send_result["date"]
        },
        "expected_reply": expected_reply
    }
    
    # Step 2: Wait for reply if expected
    if expected_reply:
        logger.info(f"Waiting for reply (timeout: {timeout}s)...")
        
        reply_result = await telegram_unified.wait_for_reply(
            sent_message_id=send_result["message_id"],
            chat_id=send_result["chat_id"],
            timeout=timeout
        )
        
        response["reply"] = reply_result
        
        if reply_result.get("status") == "reply_received":
            response["status"] = "completed_with_reply"
            logger.info(f"Reply received after {reply_result['wait_time_seconds']:.1f}s")
        elif reply_result.get("status") == "timeout":
            response["status"] = "sent_but_no_reply"
            logger.warning(f"No reply received within {timeout}s")
        else:
            response["status"] = "sent_but_error_waiting"
    
    return response


async def get_telegram_unified_status() -> Dict[str, Any]:
    """Get status of unified Telegram configuration.
    
    Returns:
        Dict with configuration and status information
    """
    return {
        "service": "telegram_unified",
        "bot_configured": config.is_telegram_configured(),
        "chat_configured": config.is_telegram_chat_configured(),
        "chat_id": config.telegram_chat_id if config.is_telegram_chat_configured() else None,
        "bot_username": "@cctrading01_bot",
        "capabilities": [
            "Send messages to configured chat",
            "Wait for replies with 1-second polling",
            "Configurable timeout (default 3 minutes)",
            "Uses environment TELEGRAM_CHAT_ID"
        ]
    }