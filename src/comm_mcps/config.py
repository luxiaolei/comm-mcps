"""Configuration management for Communications MCP."""

import os
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration for Communications MCP server."""
    
    # Email configuration
    resend_api_key: Optional[str] = Field(None, description="Resend API key")
    from_email: Optional[str] = Field(None, description="Default sender email address")
    
    # Telegram configuration
    telegram_bot_token: Optional[str] = Field(None, description="Telegram bot token")
    telegram_api_id: Optional[str] = Field(None, description="Telegram API ID")
    telegram_api_hash: Optional[str] = Field(None, description="Telegram API hash")
    telegram_chat_id: Optional[str] = Field(None, description="Default Telegram chat ID")
    
    # Signal configuration
    signal_phone_number: Optional[str] = Field(None, description="Signal phone number")
    signal_cli_path: str = Field("signal-cli", description="Path to signal-cli binary")
    
    # Server configuration
    mcp_transport: str = Field("stdio", description="MCP transport protocol")
    log_level: str = Field("INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables

    @validator("signal_phone_number")
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        if v and not (v.startswith("+") and v[1:].replace(" ", "").replace("-", "").isdigit()):
            raise ValueError("Phone number must start with + and contain only digits")
        return v
    
    @validator("from_email")
    def validate_email(cls, v):
        """Basic email validation."""
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v

    def is_email_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.resend_api_key and self.from_email)
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(self.telegram_bot_token and self.telegram_api_id and self.telegram_api_hash)
    
    def is_telegram_chat_configured(self) -> bool:
        """Check if Telegram chat ID is configured."""
        return bool(self.telegram_chat_id)
    
    def is_signal_configured(self) -> bool:
        """Check if Signal is properly configured."""
        return bool(self.signal_phone_number)


# Global configuration instance
config = Config()