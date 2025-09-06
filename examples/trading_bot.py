#!/usr/bin/env python3
"""Example: Trading Bot using Communications MCP."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from comm_mcps.tools.email import send_email
from comm_mcps.tools.telegram_unified import telegram_send_with_reply
from comm_mcps.tools.signal_unified import signal_send_with_reply


class TradingBot:
    """Example trading bot that sends notifications."""
    
    async def price_alert(self, symbol: str, price: float, change_pct: float):
        """Send price alert via multiple channels."""
        message = f"🚨 {symbol} Alert: ${price:,.2f} ({change_pct:+.1f}%)"
        
        # Send email notification
        email_result = await send_email(
            to="26442779@qq.com",
            subject=f"{symbol} Price Alert",
            body=f"Price Update:\n{symbol}: ${price:,.2f}\nChange: {change_pct:+.1f}%"
        )
        print(f"Email: {email_result.get('status')}")
        
        # Send Telegram message  
        telegram_result = await telegram_send_with_reply(
            message=message,
            expected_reply=False
        )
        print(f"Telegram: {telegram_result.get('status')}")
        
        # Send Signal message
        signal_result = await signal_send_with_reply(
            message=message,
            recipient="+8618611342177",
            expected_reply=False
        )
        print(f"Signal: {signal_result.get('status')}")
    
    async def get_user_decision(self, question: str) -> str:
        """Ask user a question via Telegram and wait for reply."""
        result = await telegram_send_with_reply(
            message=f"🤖 Trading Decision: {question}",
            expected_reply=True,
            timeout=60.0
        )
        
        if result.get("status") == "completed_with_reply":
            return result["reply"]["message"]["text"]
        else:
            return "No response"


async def main():
    """Example usage."""
    bot = TradingBot()
    
    # Example 1: Send price alerts
    print("📊 Sending price alerts...")
    await bot.price_alert("BTC", 45000.00, 5.2)
    
    # Example 2: Get user input (interactive)
    print("\n💭 Asking for trading decision...")
    decision = await bot.get_user_decision("Should we buy more BTC at current price?")
    print(f"User decision: {decision}")


if __name__ == "__main__":
    asyncio.run(main())