"""Telegram webhook support for real-time message receiving."""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, HTTPException
import uvicorn

from ..config import config

logger = logging.getLogger(__name__)


class TelegramWebhook:
    """Handles Telegram webhook setup and message receiving."""
    
    def __init__(self):
        self.app = FastAPI(title="Telegram Webhook Server")
        self.base_url = "https://api.telegram.org/bot"
        self.webhook_url = None
        self.message_handler: Optional[Callable] = None
        self.received_messages = []
        
        # Setup webhook endpoint
        @self.app.post("/webhook/telegram")
        async def webhook_handler(request: Request):
            return await self.handle_webhook(request)
    
    @property
    def bot_url(self) -> str:
        """Get the bot API URL."""
        return f"{self.base_url}{config.telegram_bot_token}"
    
    async def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Set webhook URL for the bot.
        
        Args:
            webhook_url: Public URL where webhook will receive updates
            
        Returns:
            Dict with result information
        """
        if not config.is_telegram_configured():
            return {"error": "Telegram not configured"}
        
        try:
            url = f"{self.bot_url}/setWebhook"
            data = {
                "url": webhook_url,
                "allowed_updates": ["message", "edited_message"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                result = response.json()
                
                if result.get("ok"):
                    self.webhook_url = webhook_url
                    return {
                        "status": "success",
                        "webhook_url": webhook_url,
                        "description": result.get("description", "Webhook set successfully")
                    }
                else:
                    return {"error": result.get("description", "Failed to set webhook")}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def delete_webhook(self) -> Dict[str, Any]:
        """Remove webhook and return to polling mode."""
        try:
            url = f"{self.bot_url}/deleteWebhook"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url)
                result = response.json()
                
                if result.get("ok"):
                    self.webhook_url = None
                    return {"status": "success", "message": "Webhook deleted"}
                else:
                    return {"error": result.get("description", "Failed to delete webhook")}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook information."""
        try:
            url = f"{self.bot_url}/getWebhookInfo"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                result = response.json()
                
                if result.get("ok"):
                    webhook_info = result["result"]
                    return {
                        "status": "success",
                        "webhook_url": webhook_info.get("url", ""),
                        "has_custom_certificate": webhook_info.get("has_custom_certificate", False),
                        "pending_update_count": webhook_info.get("pending_update_count", 0),
                        "last_error_date": webhook_info.get("last_error_date"),
                        "last_error_message": webhook_info.get("last_error_message"),
                        "max_connections": webhook_info.get("max_connections", 40)
                    }
                else:
                    return {"error": result.get("description", "Failed to get webhook info")}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_webhook(self, request: Request) -> Dict[str, str]:
        """Handle incoming webhook updates."""
        try:
            update = await request.json()
            
            # Process message if present
            if "message" in update:
                message = update["message"]
                
                # Store message for retrieval
                message_data = {
                    "update_id": update["update_id"],
                    "message_id": message["message_id"],
                    "text": message.get("text", ""),
                    "date": datetime.fromtimestamp(message["date"]).isoformat(),
                    "chat": {
                        "id": message["chat"]["id"],
                        "type": message["chat"]["type"],
                        "title": message["chat"].get("title"),
                        "username": message["chat"].get("username")
                    },
                    "from": {
                        "id": message["from"]["id"],
                        "username": message["from"].get("username"),
                        "first_name": message["from"].get("first_name"),
                        "last_name": message["from"].get("last_name")
                    }
                }
                
                self.received_messages.append(message_data)
                
                # Keep only last 100 messages
                if len(self.received_messages) > 100:
                    self.received_messages = self.received_messages[-100:]
                
                logger.info(f"Received message: {message.get('text', '')[:50]}...")
                
                # Call custom handler if set
                if self.message_handler:
                    await self.message_handler(message)
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.exception(f"Webhook handling error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    def get_recent_messages(self, limit: int = 10) -> Dict[str, Any]:
        """Get recently received messages from webhook."""
        messages = self.received_messages[-limit:] if self.received_messages else []
        
        return {
            "status": "success",
            "method": "webhook",
            "messages": messages,
            "count": len(messages),
            "total_stored": len(self.received_messages)
        }
    
    def set_message_handler(self, handler: Callable):
        """Set custom message handler function."""
        self.message_handler = handler
    
    def run_webhook_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the webhook server."""
        logger.info(f"Starting webhook server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Global webhook instance
telegram_webhook = TelegramWebhook()


async def setup_telegram_webhook(webhook_url: str) -> Dict[str, Any]:
    """Setup Telegram webhook.
    
    Args:
        webhook_url: Public HTTPS URL for webhook
        
    Returns:
        Dict with setup result
    """
    return await telegram_webhook.set_webhook(webhook_url)


async def get_webhook_messages(limit: int = 10) -> Dict[str, Any]:
    """Get messages received via webhook.
    
    Args:
        limit: Maximum messages to return
        
    Returns:
        Dict with messages
    """
    return telegram_webhook.get_recent_messages(limit)


def start_webhook_server(host: str = "localhost", port: int = 8000):
    """Start webhook server in background.
    
    Args:
        host: Server host
        port: Server port
    """
    telegram_webhook.run_webhook_server(host, port)