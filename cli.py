#!/usr/bin/env python3
"""Command-line interface for Communications MCP tools."""

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console

# Add src to path for imports
sys.path.insert(0, "src")

from comm_mcps.tools.email import send_email
from comm_mcps.tools.telegram_unified import telegram_send_with_reply
from comm_mcps.tools.signal_unified import signal_send_with_reply
from comm_mcps.config import config

app = typer.Typer(help="Communications MCP Command Line Interface")
console = Console()


@app.command()
def email(
    subject: str = typer.Argument(..., help="Email subject"),
    body: str = typer.Argument(..., help="Email body"),
    to: str = typer.Option("recipient@example.com", help="Recipient email")
):
    """Send email notification."""
    async def send():
        result = await send_email(to, subject, body)
        if result.get("status") == "sent":
            console.print(f"✅ Email sent to {to}", style="green")
        else:
            console.print(f"❌ Failed: {result.get('error')}", style="red")
    
    asyncio.run(send())


@app.command()
def telegram(
    message: str = typer.Argument(..., help="Message to send"),
    reply: bool = typer.Option(False, "--reply", help="Wait for reply"),
    timeout: float = typer.Option(180.0, help="Reply timeout in seconds")
):
    """Send Telegram message (bidirectional)."""
    async def send():
        result = await telegram_send_with_reply(message, reply, timeout)
        
        if result.get("status") == "sent":
            console.print("✅ Telegram message sent", style="green")
        elif result.get("status") == "completed_with_reply":
            reply_text = result["reply"]["message"]["text"]
            wait_time = result["reply"]["wait_time_seconds"]
            console.print(f"✅ Reply received ({wait_time:.1f}s): {reply_text}", style="green")
        elif result.get("status") == "sent_but_no_reply":
            console.print("📤 Message sent, no reply received", style="yellow")
        else:
            console.print(f"❌ Failed: {result.get('error')}", style="red")
    
    asyncio.run(send())


@app.command()
def signal(
    message: str = typer.Argument(..., help="Message to send"),
    recipient: str = typer.Argument(..., help="Recipient phone number"),
    reply: bool = typer.Option(False, "--reply", help="Wait for reply"),
    timeout: float = typer.Option(180.0, help="Reply timeout in seconds")
):
    """Send Signal message (bidirectional)."""
    async def send():
        result = await signal_send_with_reply(message, recipient, reply, timeout)
        
        if result.get("status") == "sent":
            console.print(f"✅ Signal message sent to {recipient}", style="green")
        elif result.get("status") == "completed_with_reply":
            reply_text = result["reply"]["message"]["text"]
            wait_time = result["reply"]["wait_time_seconds"]
            console.print(f"✅ Reply received ({wait_time:.1f}s): {reply_text}", style="green")
        elif result.get("status") == "sent_but_no_reply":
            console.print("📤 Message sent, no reply received", style="yellow")
        else:
            console.print(f"❌ Failed: {result.get('error')}", style="red")
    
    asyncio.run(send())


@app.command()
def status():
    """Check configuration status of all services."""
    async def check():
        from comm_mcps.tools.email import get_email_status
        from comm_mcps.tools.telegram_unified import get_telegram_unified_status
        from comm_mcps.tools.signal_unified import get_signal_unified_status
        
        email_status = await get_email_status()
        telegram_status = await get_telegram_unified_status()
        signal_status = await get_signal_unified_status()
        
        console.print("📊 Service Status:", style="bold")
        console.print(f"📧 Email: {'✅' if email_status['configured'] else '❌'}")
        console.print(f"📱 Telegram: {'✅' if telegram_status['bot_configured'] else '❌'}")  
        console.print(f"💬 Signal: {'✅' if signal_status['configured'] else '❌'}")
    
    asyncio.run(check())


if __name__ == "__main__":
    app()