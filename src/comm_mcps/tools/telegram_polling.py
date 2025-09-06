"""Telegram message receiving via polling (getUpdates API)."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx

from ..config import config

logger = logging.getLogger(__name__)


class TelegramPolling:
    """Handles Telegram message receiving via polling."""
    
    def __init__(self):
        self.base_url = "https://api.telegram.org/bot"
        self.offset = 0
        self.running = False
    
    @property
    def bot_url(self) -> str:
        """Get the bot API URL."""
        return f"{self.base_url}{config.telegram_bot_token}"
    
    async def get_updates(self, timeout: int = 10, limit: int = 100) -> Dict[str, Any]:
        """Get updates from Telegram using getUpdates API.
        
        Args:
            timeout: Timeout for long polling
            limit: Maximum number of updates to retrieve
            
        Returns:
            Dict with updates or error information
        """
        if not config.is_telegram_configured():
            return {"error": "Telegram not configured"}
        
        try:
            params = {
                "offset": self.offset,
                "limit": limit,
                "timeout": timeout,
                "allowed_updates": ["message", "edited_message"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_url}/getUpdates",
                    params=params,
                    timeout=timeout + 5
                )
                
                data = response.json()
                
                if data.get("ok"):
                    updates = data.get("result", [])
                    
                    # Update offset for next polling
                    if updates:
                        self.offset = updates[-1]["update_id"] + 1
                    
                    return {
                        "status": "success",
                        "updates": updates,
                        "count": len(updates)
                    }
                else:
                    error_msg = data.get("description", "Unknown API error")
                    logger.error(f"Telegram API error: {error_msg}")
                    return {"error": f"API error: {error_msg}"}
                    
        except httpx.TimeoutException:
            return {"error": "Request timeout"}
        except Exception as e:
            logger.exception(f"Error getting updates: {e}")
            return {"error": str(e)}
    
    async def get_recent_messages(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent messages from Telegram.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            Dict with messages and metadata
        """
        result = await self.get_updates(timeout=5, limit=limit)
        
        if "error" in result:
            return result
        
        messages = []
        updates = result.get("updates", [])
        
        for update in updates:
            if "message" in update:
                msg = update["message"]
                
                message_data = {
                    "update_id": update["update_id"],
                    "message_id": msg["message_id"],
                    "text": msg.get("text", ""),
                    "date": datetime.fromtimestamp(msg["date"]).isoformat(),
                    "chat": {
                        "id": msg["chat"]["id"],
                        "type": msg["chat"]["type"],
                        "title": msg["chat"].get("title"),
                        "username": msg["chat"].get("username")
                    },
                    "from": {
                        "id": msg["from"]["id"],
                        "username": msg["from"].get("username"),
                        "first_name": msg["from"].get("first_name"),
                        "last_name": msg["from"].get("last_name")
                    }
                }
                
                messages.append(message_data)
        
        return {
            "status": "success",
            "messages": messages,
            "count": len(messages),
            "bot_info": {
                "username": "@cctrading01_bot",
                "url": "https://t.me/cctrading01_bot"
            }
        }
    
    async def start_polling(self, message_handler=None):
        """Start continuous polling for messages.
        
        Args:
            message_handler: Optional function to handle incoming messages
        """
        self.running = True
        logger.info("Starting Telegram polling...")
        
        while self.running:
            try:
                result = await self.get_updates(timeout=30)
                
                if result.get("status") == "success":
                    updates = result.get("updates", [])
                    
                    for update in updates:
                        if "message" in update and message_handler:
                            await message_handler(update["message"])
                        
                        logger.info(f"Processed update {update['update_id']}")
                
                elif "error" in result:
                    logger.error(f"Polling error: {result['error']}")
                    await asyncio.sleep(5)  # Wait before retrying
                    
            except Exception as e:
                logger.exception(f"Polling exception: {e}")
                await asyncio.sleep(5)
    
    def stop_polling(self):
        """Stop the polling loop."""
        self.running = False
        logger.info("Stopping Telegram polling...")


# Global polling instance
telegram_polling = TelegramPolling()


async def receive_telegram_messages_polling(
    timeout: float = 30.0,
    limit: int = 10
) -> Dict[str, Any]:
    """Receive messages using polling method.
    
    Args:
        timeout: How long to wait for new messages
        limit: Maximum messages to retrieve
        
    Returns:
        Dict with messages or error information
    """
    if not config.is_telegram_configured():
        return {
            "status": "error",
            "error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN"
        }
    
    logger.info(f"Polling for Telegram messages (timeout: {timeout}s)")
    
    try:
        # Get recent messages using polling
        result = await telegram_polling.get_recent_messages(limit=limit)
        
        if result.get("status") == "success":
            messages = result.get("messages", [])
            logger.info(f"Retrieved {len(messages)} messages via polling")
            
            return {
                "status": "success",
                "method": "polling",
                "messages": messages,
                "count": len(messages),
                "instructions": [
                    "Messages are retrieved using Telegram Bot API polling",
                    "Send messages to @cctrading01_bot to test",
                    "Bot will receive messages sent after the last poll"
                ]
            }
        else:
            return result
            
    except Exception as e:
        error_msg = f"Polling failed: {str(e)}"
        logger.exception(error_msg)
        return {"status": "error", "error": error_msg}


async def send_message_via_api(chat_id: str, text: str) -> Dict[str, Any]:
    """Send message using direct HTTP API call.
    
    Args:
        chat_id: Target chat ID
        text: Message text
        
    Returns:
        Dict with result information
    """
    if not config.is_telegram_configured():
        return {"error": "Telegram not configured"}
    
    try:
        url = f"{telegram_polling.bot_url}/sendMessage"
        
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            result = response.json()
            
            if result.get("ok"):
                return {
                    "status": "sent",
                    "message_id": result["result"]["message_id"],
                    "chat_id": chat_id
                }
            else:
                return {"error": result.get("description", "Send failed")}
                
    except Exception as e:
        return {"error": str(e)}