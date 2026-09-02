"""
Export Tokens Plugin
Adds export functionality without modifying core code
"""
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from plugins import register_hook, call_hook
from database import db


@register_hook("on_admin_panel")
async def add_export_button(keyboard, context):
    """Add Export button to admin panel"""
    keyboard.append([
        InlineKeyboardButton("📤 Export Tokens", callback_data="export_tokens"),
        InlineKeyboardButton("📊 Stats", callback_data="show_stats")
    ])
    return keyboard


@register_hook("on_export")
async def after_export(filepath, admin_id):
    """Log export activity"""
    print(f"[Export Plugin] Tokens exported to {filepath} for admin {admin_id}")
