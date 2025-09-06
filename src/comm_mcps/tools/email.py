"""Email communication tool using Resend API."""

import logging
from typing import Dict, Optional

import httpx
import resend

from ..config import config

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Exception raised for email-related errors."""
    pass


async def send_email(
    to: str,
    subject: str,
    body: str,
    expected_reply: bool = False,
    timeout: float = 180.0,
    from_email: Optional[str] = None,
    html_body: Optional[str] = None
) -> Dict[str, str]:
    """Send an email using Resend API.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email content
        expected_reply: Whether to expect a reply (not used for email, always False)
        timeout: Request timeout in seconds (default 3 minutes)
        from_email: Optional sender email (overrides config)
        html_body: Optional HTML version of the email
    
    Returns:
        Dict with status, message_id, and any error information
    """
    if not config.is_email_configured():
        return {
            "status": "error",
            "error": "Email not configured. Set RESEND_API_KEY and FROM_EMAIL in .env"
        }
    
    # Validate email addresses
    if "@" not in to:
        return {"status": "error", "error": "Invalid recipient email address"}
    
    sender_email = from_email or config.from_email
    if not sender_email or "@" not in sender_email:
        return {"status": "error", "error": "Invalid sender email address"}
    
    try:
        # Configure Resend client
        resend.api_key = config.resend_api_key
        
        # Prepare email parameters
        email_params = {
            "from": sender_email,
            "to": [to],
            "subject": subject,
            "text": body,
        }
        
        # Add HTML content if provided
        if html_body:
            email_params["html"] = html_body
        
        logger.info(f"Sending email to {to} with subject: {subject[:50]}...")
        
        # Send email with timeout
        response = resend.Emails.send(email_params)
        
        if hasattr(response, 'error') and response.error:
            error_msg = f"Resend API error: {response.error}"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}
        
        message_id = getattr(response, 'id', 'unknown')
        logger.info(f"Email sent successfully. Message ID: {message_id}")
        
        return {
            "status": "sent",
            "message_id": message_id,
            "recipient": to,
            "subject": subject
        }
        
    except httpx.TimeoutException:
        error_msg = f"Email send timeout after {timeout} seconds"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.exception(error_msg)
        return {"status": "error", "error": error_msg}


async def get_email_status() -> Dict[str, str]:
    """Get email service configuration status.
    
    Returns:
        Dict with configuration status information
    """
    status = {
        "service": "email",
        "provider": "resend",
        "configured": config.is_email_configured()
    }
    
    if config.is_email_configured():
        status.update({
            "from_email": config.from_email,
            "api_key_configured": bool(config.resend_api_key)
        })
    else:
        status["error"] = "Missing RESEND_API_KEY or FROM_EMAIL configuration"
    
    return status