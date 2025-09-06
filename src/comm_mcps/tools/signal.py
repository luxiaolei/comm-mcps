"""Signal communication tool using signal-cli wrapper."""

import asyncio
import json
import logging
import shlex
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..config import config

logger = logging.getLogger(__name__)


class SignalError(Exception):
    """Exception raised for Signal-related errors."""
    pass


@dataclass
class SignalMessage:
    """Represents a Signal message."""
    message: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: Optional[str] = None
    group_name: Optional[str] = None
    error: Optional[str] = None


async def _run_signal_cli(cmd: str, timeout: float = 30.0) -> Tuple[str, str, Optional[int]]:
    """Run signal-cli command with timeout.
    
    Args:
        cmd: Command to execute
        timeout: Command timeout in seconds
    
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        return stdout.decode(), stderr.decode(), process.returncode
        
    except asyncio.TimeoutError:
        logger.error(f"Signal CLI command timeout after {timeout} seconds")
        if 'process' in locals():
            process.kill()
        return "", "Command timeout", -1
        
    except Exception as e:
        logger.exception(f"Error running signal-cli: {e}")
        return "", str(e), -1


def _parse_signal_output(output: str) -> List[SignalMessage]:
    """Parse signal-cli output into SignalMessage objects.
    
    Args:
        output: Raw output from signal-cli
    
    Returns:
        List of parsed SignalMessage objects
    """
    messages = []
    
    try:
        # Signal CLI outputs JSON lines for received messages
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                
                # Handle different message types
                if 'envelope' in data:
                    envelope = data['envelope']
                    message = SignalMessage(
                        message=envelope.get('dataMessage', {}).get('message'),
                        sender=envelope.get('source'),
                        timestamp=envelope.get('timestamp'),
                        group_name=envelope.get('dataMessage', {}).get('groupInfo', {}).get('groupId')
                    )
                    messages.append(message)
                    
            except json.JSONDecodeError:
                # Handle plain text output
                if "Envelope from:" in line:
                    # Parse plain text format
                    message = SignalMessage()
                    lines = output.split('\n')
                    
                    for i, text_line in enumerate(lines):
                        if "Envelope from:" in text_line:
                            message.sender = text_line.split("Envelope from:")[1].strip()
                        elif "Body:" in text_line:
                            message.message = text_line.split("Body:")[1].strip()
                        elif "Timestamp:" in text_line:
                            message.timestamp = text_line.split("Timestamp:")[1].strip()
                    
                    if message.sender or message.message:
                        messages.append(message)
                    break
                    
    except Exception as e:
        logger.exception(f"Error parsing Signal output: {e}")
        messages.append(SignalMessage(error=f"Failed to parse output: {str(e)}"))
    
    return messages


async def send_signal_message(
    message: str,
    recipient: str,
    expected_reply: bool = False,
    timeout: float = 180.0
) -> Dict[str, str]:
    """Send a message via Signal.
    
    Args:
        message: Message content to send
        recipient: Recipient phone number (e.g., +1234567890)
        expected_reply: Whether to expect a reply (for future polling)
        timeout: Operation timeout in seconds (default 3 minutes)
    
    Returns:
        Dict with status and any error information
    """
    if not config.is_signal_configured():
        return {
            "status": "error",
            "error": "Signal not configured. Set SIGNAL_PHONE_NUMBER in .env"
        }
    
    # Validate recipient format
    if not recipient.startswith('+'):
        return {"status": "error", "error": "Recipient must be a phone number starting with +"}
    
    try:
        # Build signal-cli send command
        cmd = (
            f"{shlex.quote(config.signal_cli_path)} "
            f"-u {shlex.quote(config.signal_phone_number)} "
            f"send -m {shlex.quote(message)} {shlex.quote(recipient)}"
        )
        
        logger.info(f"Sending Signal message to {recipient}")
        stdout, stderr, return_code = await _run_signal_cli(cmd, timeout)
        
        if return_code != 0:
            error_msg = f"Signal CLI failed: {stderr or 'Unknown error'}"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}
        
        logger.info(f"Signal message sent successfully to {recipient}")
        
        return {
            "status": "sent",
            "recipient": recipient,
            "expected_reply": expected_reply,
            "message": message[:50] + "..." if len(message) > 50 else message
        }
        
    except Exception as e:
        error_msg = f"Failed to send Signal message: {str(e)}"
        logger.exception(error_msg)
        return {"status": "error", "error": error_msg}


async def receive_signal_messages(
    timeout: float = 180.0
) -> Dict[str, any]:
    """Receive messages from Signal.
    
    Args:
        timeout: How long to wait for messages (default 3 minutes)
    
    Returns:
        Dict with messages list and any error information
    """
    if not config.is_signal_configured():
        return {
            "status": "error",
            "error": "Signal not configured. Set SIGNAL_PHONE_NUMBER in .env"
        }
    
    try:
        # Build signal-cli receive command with timeout
        cmd = (
            f"{shlex.quote(config.signal_cli_path)} "
            f"-u {shlex.quote(config.signal_phone_number)} "
            f"receive --timeout {int(timeout)}"
        )
        
        logger.info(f"Waiting for Signal messages (timeout: {timeout}s)")
        stdout, stderr, return_code = await _run_signal_cli(cmd, timeout + 10)
        
        if return_code != 0:
            # Timeout is expected when no messages
            if "timeout" in stderr.lower() or return_code == 1:
                logger.info("No Signal messages received within timeout")
                return {
                    "status": "success",
                    "messages": [],
                    "count": 0
                }
            else:
                error_msg = f"Signal CLI failed: {stderr or 'Unknown error'}"
                logger.error(error_msg)
                return {"status": "error", "error": error_msg}
        
        # Parse received messages
        messages = _parse_signal_output(stdout)
        
        # Convert to dict format
        message_dicts = []
        for msg in messages:
            if msg.error:
                return {"status": "error", "error": msg.error}
            
            message_dict = {
                "message": msg.message,
                "sender": msg.sender,
                "timestamp": msg.timestamp
            }
            
            if msg.group_name:
                message_dict["group_name"] = msg.group_name
            
            message_dicts.append(message_dict)
        
        logger.info(f"Received {len(message_dicts)} Signal messages")
        
        return {
            "status": "success",
            "messages": message_dicts,
            "count": len(message_dicts)
        }
        
    except Exception as e:
        error_msg = f"Failed to receive Signal messages: {str(e)}"
        logger.exception(error_msg)
        return {"status": "error", "error": error_msg}


async def get_signal_status() -> Dict[str, str]:
    """Get Signal service configuration status.
    
    Returns:
        Dict with configuration status information
    """
    status = {
        "service": "signal",
        "configured": config.is_signal_configured()
    }
    
    if config.is_signal_configured():
        status.update({
            "phone_number": config.signal_phone_number,
            "cli_path": config.signal_cli_path
        })
        
        # Test if signal-cli is available
        try:
            cmd = f"{shlex.quote(config.signal_cli_path)} --version"
            stdout, stderr, return_code = await _run_signal_cli(cmd, 10)
            
            if return_code == 0:
                status["cli_available"] = True
                status["cli_version"] = stdout.strip()
            else:
                status["cli_available"] = False
                status["cli_error"] = stderr.strip()
                
        except Exception as e:
            status["cli_available"] = False
            status["cli_error"] = str(e)
    else:
        status["error"] = "Missing SIGNAL_PHONE_NUMBER configuration"
    
    return status