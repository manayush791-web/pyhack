"""
Sample Plugin: Auto-Reply Feature
Demonstrates how to add features without modifying core code.

This plugin adds an auto-reply feature: when any user sends "hello"
to a managed bot, it replies with a premium greeting.
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from plugins import register_hook


@register_hook("on_text_received")
async def auto_reply_hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-reply to 'hello' messages on managed bots"""
    if not update.message or not update.message.text:
        return False

    text = update.message.text.lower()
    if "hello" in text or "hi" in text or "hey" in text:
        await update.message.reply_text(
            "👋 <b>Hey there!</b> 👋\n\n"
            "✨ Welcome! Tap any emoji to see it animate! ✨\n"
            "🎉 🎊 🎈 💖 🔥 💫 🌈 ☄️",
            parse_mode=ParseMode.HTML
        )
        return True  # Block further processing

    return False  # Allow other handlers


@register_hook("on_user_joined")
async def log_join(user_id, bot_token):
    """Log when users join"""
    print(f"[AutoReply Plugin] User {user_id} started bot {bot_token[:15]}...")
