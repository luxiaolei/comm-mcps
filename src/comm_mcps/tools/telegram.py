"""Telegram communication tool with bidirectional messaging."""

import asyncio
import logging
from typing import Dict, List, Optional

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.sessions import StringSession

from ..config import config

logger = logging.getLogger(__name__)


class TelegramError(Exception):
    """Exception raised for Telegram-related errors."""
    pass


class TelegramManager:
    """Manages Telegram client connection and operations."""
    
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Telegram client.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
            
        if not config.is_telegram_configured():
            logger.error("Telegram not configured")
            return False
        
        try:
            # Create client with bot token authentication
            self.client = TelegramClient(
                StringSession(),
                int(config.telegram_api_id),
                config.telegram_api_hash
            )
            
            await self.client.start(bot_token=config.telegram_bot_token)
            self._initialized = True
            logger.info("Telegram client initialized successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to initialize Telegram client: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect the Telegram client."""
        if self.client:
            await self.client.disconnect()
            self._initialized = False


# Global Telegram manager instance
telegram_manager = TelegramManager()


async def send_telegram_message(
    message: str,
    chat_id: str,
    expected_reply: bool = False,
    timeout: float = 180.0
) -> Dict[str, str]:
    """Send a message via Telegram.
    
    Args:
        message: Message content to send
        chat_id: Target chat ID (username or numeric ID)
        expected_reply: Whether to expect a reply (for future polling)
        timeout: Operation timeout in seconds (default 3 minutes)
    
    Returns:
        Dict with status, message_id, and any error information
    """
    if not await telegram_manager.initialize():
        return {
            "status": "error",
            "error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN, TELEGRAM_API_ID, and TELEGRAM_API_HASH"
        }
    
    try:
        # Send message with timeout
        async with asyncio.timeout(timeout):
            sent_message = await telegram_manager.client.send_message(chat_id, message)
            
            logger.info(f"Telegram message sent to {chat_id}")
            
            return {
                "status": "sent",
                "message_id": str(sent_message.id),
                "chat_id": chat_id,
                "expected_reply": expected_reply
            }
            
    except asyncio.TimeoutError:
        error_msg = f"Telegram send timeout after {timeout} seconds"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}
        
    except Exception as e:
        error_msg = f"Failed to send Telegram message: {str(e)}"
        logger.exception(error_msg)
        return {"status": "error", "error": error_msg}


async def receive_telegram_messages(
    chat_id: Optional[str] = None,
    limit: int = 10,
    timeout: float = 180.0
) -> Dict[str, any]:
    """Attempt to receive recent messages from Telegram.
    
    Note: Telegram Bot API has significant limitations:
    - Bots cannot access message history in most chats
    - Bots only receive messages sent directly to them
    - This function explains the limitation and suggests alternatives
    
    Args:
        chat_id: Specific chat to get messages from (optional)
        limit: Maximum number of messages to retrieve
        timeout: Operation timeout in seconds (default 3 minutes)
    
    Returns:
        Dict with limitation info and suggestions
    """
    if not await telegram_manager.initialize():
        return {
            "status": "error",
            "error": "Telegram not configured"
        }
    
    # Return explanation of bot limitations
    return {
        "status": "limited",
        "info": "Telegram Bot API Limitation",
        "explanation": "Bots cannot retrieve message history from chats. Bots only receive messages when users actively send them to the bot.",
        "suggestions": [
            "Users should send messages directly to @cctrading01_bot",
            "Add the bot to a group and users can interact with it there",
            "Messages sent to the bot will be processed in real-time",
            "For message retrieval, consider using webhooks or user account (not bot) mode"
        ],
        "bot_username": "@cctrading01_bot",
        "bot_url": "https://t.me/cctrading01_bot"
    }


async def get_telegram_chats(limit: int = 20) -> Dict[str, any]:
    """Get information about Telegram bot capabilities.
    
    Note: Bot API limitations prevent listing chats like user accounts can.
    
    Args:
        limit: Ignored for bot API
    
    Returns:
        Dict with bot information and usage instructions
    """
    if not await telegram_manager.initialize():
        return {
            "status": "error",
            "error": "Telegram not configured"
        }
    
    # Return bot usage information instead of trying to list chats
    return {
        "status": "info",
        "info": "Bot API Usage Information",
        "bot_username": "@cctrading01_bot",
        "bot_url": "https://t.me/cctrading01_bot",
        "capabilities": [
            "Send messages to users who have started the bot",
            "Send messages to groups where the bot is added",
            "Receive and respond to messages sent to the bot"
        ],
        "usage_instructions": [
            "Users must first send /start to the bot",
            "Use the bot username @cctrading01_bot as chat_id for sending",
            "For groups, add the bot and use the group's chat_id",
            "Bots cannot initiate conversations with users who haven't started the bot"
        ],
        "limitation": "Bots cannot list or browse chats like user accounts. They can only interact with chats where they've been explicitly added or started by users."
    }


async def get_telegram_status() -> Dict[str, str]:
    """Get Telegram service configuration status.
    
    Returns:
        Dict with configuration status information
    """
    status = {
        "service": "telegram",
        "configured": config.is_telegram_configured(),
        "connected": telegram_manager._initialized
    }
    
    if config.is_telegram_configured():
        status.update({
            "api_id_configured": bool(config.telegram_api_id),
            "api_hash_configured": bool(config.telegram_api_hash),
            "bot_token_configured": bool(config.telegram_bot_token)
        })
    else:
        status["error"] = "Missing TELEGRAM_BOT_TOKEN, TELEGRAM_API_ID, or TELEGRAM_API_HASH configuration"
    
    return status