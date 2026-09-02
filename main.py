import sys, os
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path: sys.path.insert(0, PROJECT_DIR)
"""
Telegram Bot Manager - Main Admin Bot
Run this file to start the management panel.

Features:
- Add multiple bot tokens (line by line, with/without quotes)
- Start/Stop/Delete managed bots
- Broadcast to ALL users across ALL bots
- Check admin rights in groups
- Clone bot settings
- Export tokens to file
- Plugin system for extensibility
- Premium UI/UX with animated emoji
"""
import os
import sys
import re
import json
import asyncio
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardRemove, Bot
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

from config import (
    ADMIN_IDS, STATE_IDLE, STATE_WAITING_TOKENS, STATE_WAITING_BROADCAST,
    STATE_WAITING_WELCOME, STATE_WAITING_BUTTONS, STATE_WAITING_CHANNEL,
    STATE_WAITING_CLONE_SOURCE, STATE_WAITING_CLONE_TARGET, DEFAULT_BUTTONS
)
from database import db
from managed_bot import (
    start_managed_bot, stop_managed_bot, stop_all_managed_bots,
    get_running_bots, is_bot_running
)
from plugins import load_plugins, call_hook

# ============ INITIALIZATION ============
# Load all plugins on startup
load_plugins()

# Store admin bot application globally
_admin_app = None


def is_authorized(user_id: int) -> bool:
    """Check if user is admin"""
    if user_id in ADMIN_IDS:
        return True
    return db.is_admin(user_id)


def parse_tokens(text: str) -> list:
    """
    Parse bot tokens from text.
    Supports:
    - Line by line tokens
    - Tokens in single/double quotes
    - Mixed formats
    """
    tokens = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove surrounding quotes (single or double)
        if (line.startswith('"') and line.endswith('"')) or \
           (line.startswith("'") and line.endswith("'")):
            line = line[1:-1]

        # Validate token format (typically 123456:ABC-DEF...)
        if re.match(r'^\d+:[A-Za-z0-9_-]+$', line):
            tokens.append(line)

    return tokens


# ============ KEYBOARD BUILDERS ============
def build_admin_panel(context: ContextTypes.DEFAULT_TYPE = None):
    """Build the main admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Bot Tokens", callback_data="add_tokens")],
        [InlineKeyboardButton("🚀 Start Bot", callback_data="start_bot"),
         InlineKeyboardButton("🛑 Stop Bot", callback_data="stop_bot")],
        [InlineKeyboardButton("📋 List Bots", callback_data="list_bots"),
         InlineKeyboardButton("🗑️ Delete Bot", callback_data="delete_bot")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
         InlineKeyboardButton("👮 Check Admin", callback_data="check_admin")],
        [InlineKeyboardButton("🔄 Clone Bot", callback_data="clone_bot"),
         InlineKeyboardButton("✏️ Edit Welcome", callback_data="edit_welcome")],
        [InlineKeyboardButton("🔘 Edit Buttons", callback_data="edit_buttons")],
    ]

    # Allow plugins to modify the keyboard
    if context:
        try:
            loop = asyncio.get_event_loop()
            # Hooks are async, but keyboard builder is sync
            # We'll append plugin buttons statically for now
            keyboard.append([
                InlineKeyboardButton("📤 Export Tokens", callback_data="export_tokens"),
                InlineKeyboardButton("📊 Stats", callback_data="show_stats")
            ])
        except:
            pass

    return InlineKeyboardMarkup(keyboard)


def build_bot_list_keyboard(action="select"):
    """Build keyboard with all stored bots"""
    bots = db.get_all_bots()
    keyboard = []

    for bot in bots:
        status = "🟢" if bot["status"] == "running" else "🔴"
        label = f"{status} @{bot['username'] or 'Unknown'}" if bot["username"] else f"{status} {bot['token'][:20]}..."
        keyboard.append([InlineKeyboardButton(label, callback_data=f"{action}:{bot['token']}")])

    keyboard.append([InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)


# ============ HANDLERS ============
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start - Show admin panel or reject"""
    user = update.effective_user

    if not is_authorized(user.id):
        await update.message.reply_text(
            "⛔ <b>Access Denied</b>\n\n"
            "You are not authorized to use this bot.\n"
            "Contact the administrator.",
            parse_mode=ParseMode.HTML
        )
        return STATE_IDLE

    # Add to admins table if not already
    db.add_admin(user.id)

    welcome_text = f"""
{random_premium_header()}

<b>👑 Welcome to Bot Manager, {user.first_name}!</b>

🎉 <b>Premium Bot Management Panel</b> 🎉

<i>Manage unlimited Telegram bots from one place!</i>

💎 <b>Features:</b>
• Add multiple bots (line by line)
• Start/Stop/Delete bots
• Broadcast to ALL users
• Check admin rights
• Clone bot settings
• Export tokens
• Plugin system

<b>Choose an action below:</b>
"""

    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_admin_panel(context)
    )
    return STATE_IDLE


def random_premium_header():
    """Generate random premium header decoration"""
    import random
    headers = [
        "✨ 🌟 💎 🌟 ✨",
        "🎉 🔥 👑 🔥 🎉",
        "💖 ⚡ 🌈 ⚡ 💖",
        "🎊 🏆 💫 🏆 🎊",
        "🌈 ☄️ ✨ ☄️ 🌈"
    ]
    return random.choice(headers)


async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    query = update.callback_query
    await query.answer()

    text = f"""
{random_premium_header()}

<b>🎛️ Admin Control Panel</b>

<i>Select an action to manage your bots</i>
"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_admin_panel(context)
    )
    return STATE_IDLE


# ============ ADD TOKENS ============
async def add_tokens_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to send tokens"""
    query = update.callback_query
    await query.answer()

    text = """
<b>➕ Add Bot Tokens</b>

Send me bot tokens in any format:
• One per line
• With or without quotes
• Single or double quotes accepted

<b>Example:</b>
<code>123456789:ABCdefGHIjklMNOpqrSTUvwxyz</code>
<code>"987654321:XYZabcDEFghiJKLmnoPQRstu"</code>
<code>'456789123:LMNopqRSTuvwXYZabcDEFghi'</code>

<i>You can send multiple tokens at once!</i>
"""

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return STATE_WAITING_TOKENS


async def receive_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and process bot tokens"""
    text = update.message.text
    tokens = parse_tokens(text)

    if not tokens:
        await update.message.reply_text(
            "❌ <b>No valid tokens found!</b>\n"
            "Please send tokens in correct format.",
            parse_mode=ParseMode.HTML
        )
        return STATE_WAITING_TOKENS

    results = []
    for token in tokens:
        try:
            # Validate token by getting bot info
            temp_bot = Bot(token)
            me = await temp_bot.get_me()

            # Store in database
            db.add_bot(token, username=me.username)

            # Call plugin hook
            await call_hook("on_bot_added", token, me.username)

            results.append(f"✅ @{me.username} ({me.first_name})")

            # Clean up temp bot session
            await temp_bot.session.close()

        except Exception as e:
            results.append(f"❌ Invalid token: ...{token[-15:]} | Error: {str(e)[:50]}")

    # Send results line by line as requested
    result_text = f"<b>📋 Token Processing Results ({len(tokens)} found)</b>\n\n"
    result_text += "\n".join(results)

    await update.message.reply_text(
        result_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )

    return STATE_IDLE


# ============ START BOT ============
async def start_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of bots to start"""
    query = update.callback_query
    await query.answer()

    bots = db.get_all_bots()
    if not bots:
        await query.edit_message_text(
            "❌ No bots found. Add tokens first!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    await query.edit_message_text(
        "<b>🚀 Select a bot to START:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=build_bot_list_keyboard("do_start")
    )
    return STATE_IDLE


async def do_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start selected bot"""
    query = update.callback_query
    await query.answer("Starting bot...")

    data = query.data.split(":", 1)
    if len(data) < 2:
        return STATE_IDLE

    token = data[1]

    if is_bot_running(token):
        await query.edit_message_text(
            "⚠️ Bot is already running!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    success, result = await start_managed_bot(token)

    if success:
        text = f"""
✅ <b>Bot Started Successfully!</b>

👤 <b>Username:</b> @{result}
🔑 <b>Token:</b> <code>{token[:15]}...</code>
📊 <b>Status:</b> 🟢 Running

<i>The bot is now live and welcoming users!</i>
"""
    else:
        text = f"""
❌ <b>Failed to Start Bot</b>

🔑 <b>Token:</b> <code>{token[:15]}...</code>
🚨 <b>Error:</b> <code>{result}</code>
"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


# ============ STOP BOT ============
async def stop_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of running bots to stop"""
    query = update.callback_query
    await query.answer()

    running = get_running_bots()
    if not running:
        await query.edit_message_text(
            "❌ No bots are currently running.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    keyboard = []
    for token, info in running.items():
        label = f"🛑 @{info['username']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"do_stop:{token}")])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])

    await query.edit_message_text(
        "<b>🛑 Select a bot to STOP:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_IDLE


async def do_stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop selected bot"""
    query = update.callback_query
    await query.answer("Stopping bot...")

    data = query.data.split(":", 1)
    if len(data) < 2:
        return STATE_IDLE

    token = data[1]
    success, result = await stop_managed_bot(token)

    if success:
        text = f"✅ <b>Bot Stopped:</b> @{result}"
    else:
        text = f"❌ <b>Error:</b> {result}"

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


# ============ LIST BOTS ============
async def list_bots_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all stored bots"""
    query = update.callback_query
    await query.answer()

    bots = db.get_all_bots()
    if not bots:
        await query.edit_message_text(
            "📭 No bots found. Add some tokens first!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    lines = [f"<b>📋 Your Bot Collection ({len(bots)} total)</b>\n"]

    for i, bot in enumerate(bots, 1):
        status = "🟢 RUNNING" if bot["status"] == "running" else "🔴 STOPPED"
        username = f"@{bot['username']}" if bot["username"] else "Unknown"
        token_preview = bot["token"][:20] + "..."

        lines.append(
            f"{i}. <b>{username}</b>\n"
            f"   ├ Status: {status}\n"
            f"   ├ Token: <code>{token_preview}</code>\n"
            f"   └ Added: {bot['created_at']}\n"
        )

    text = "\n".join(lines)

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


# ============ DELETE BOT ============
async def delete_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of bots to delete"""
    query = update.callback_query
    await query.answer()

    bots = db.get_all_bots()
    if not bots:
        await query.edit_message_text(
            "❌ No bots to delete.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    await query.edit_message_text(
        "<b>🗑️ Select a bot to DELETE (permanent):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=build_bot_list_keyboard("do_delete")
    )
    return STATE_IDLE


async def do_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete selected bot"""
    query = update.callback_query
    await query.answer("Deleting...")

    data = query.data.split(":", 1)
    if len(data) < 2:
        return STATE_IDLE

    token = data[1]

    # Stop if running
    if is_bot_running(token):
        await stop_managed_bot(token)

    db.delete_bot(token)

    await query.edit_message_text(
        "🗑️ <b>Bot deleted successfully!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


# ============ BROADCAST ============
async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate broadcast flow"""
    query = update.callback_query
    await query.answer()

    total_users = db.get_total_users_all_bots()

    text = f"""
<b>📢 Broadcast Message</b>

👥 <b>Total users to reach:</b> {total_users}

Send me the message you want to broadcast.

<b>Supported formats:</b>
• Plain text
• HTML formatting
• Emoji & animated emoji

<i>This will be sent to EVERY user who ever started ANY of your bots.</i>
"""

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return STATE_WAITING_BROADCAST


async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and send broadcast"""
    message = update.message
    broadcast_text = message.text

    # Get all users grouped by bot token
    all_users = db.get_all_users()

    if not all_users:
        await message.reply_text(
            "❌ No users found to broadcast to.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    # Group users by bot token
    from managed_bot import _running_bots

    status_msg = await message.reply_text(
        f"⏳ <b>Broadcasting...</b>\n"
        f"Total users: {len(all_users)}\n"
        f"Please wait...",
        parse_mode=ParseMode.HTML
    )

    sent = 0
    failed = 0

    # Use running bot instances to send messages
    for user_info in all_users:
        user_id = user_info["user_id"]
        chat_id = user_info["chat_id"]
        bot_token = user_info["bot_token"]

        try:
            if bot_token in _running_bots:
                bot = _running_bots[bot_token]["bot"]
                await bot.send_message(
                    chat_id=chat_id,
                    text=broadcast_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                sent += 1
            else:
                # Bot not running, try with admin bot
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=broadcast_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                sent += 1
        except Exception as e:
            failed += 1
            print(f"Broadcast failed to {user_id}: {e}")

        # Update status every 50 messages
        if (sent + failed) % 50 == 0:
            try:
                await status_msg.edit_text(
                    f"⏳ <b>Broadcasting...</b>\n"
                    f"Sent: {sent} | Failed: {failed}\n"
                    f"Progress: {sent + failed}/{len(all_users)}",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass

    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"👥 Total: {len(all_users)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )

    # Call plugin hooks
    await call_hook("on_broadcast_sent", "all", sent)

    return STATE_IDLE


# ============ CHECK ADMIN ============
async def check_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for group/channel to check admin status"""
    query = update.callback_query
    await query.answer()

    text = """
<b>👮 Check Admin Rights</b>

Send me the group/channel ID or username.

<b>Examples:</b>
<code>-1001234567890</code> (channel ID)
<code>@mygroup</code> (group username)

<i>I will check if any of your managed bots are admin there.</i>
"""

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return STATE_WAITING_CHANNEL


async def receive_channel_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check admin status in channel/group"""
    channel = update.message.text.strip()

    from managed_bot import _running_bots

    results = []
    for token, info in _running_bots.items():
        try:
            bot = info["bot"]
            member = await bot.get_chat_member(channel, info["id"])
            status = member.status

            if status in ["administrator", "creator"]:
                results.append(f"✅ @{info['username']} - <b>{status.upper()}</b>")
            else:
                results.append(f"❌ @{info['username']} - {status}")
        except Exception as e:
            results.append(f"⚠️ @{info['username']} - Error: {str(e)[:30]}")

    if not results:
        text = "❌ No running bots to check."
    else:
        text = f"<b>👮 Admin Check Results for {channel}</b>\n\n" + "\n".join(results)

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


# ============ CLONE BOT ============
async def clone_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate bot clone"""
    query = update.callback_query
    await query.answer()

    text = """
<b>🔄 Clone Bot Settings</b>

Send me the <b>source</b> bot token (the one to copy FROM).
"""

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return STATE_WAITING_CLONE_SOURCE


async def receive_clone_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive source token for cloning"""
    token = update.message.text.strip().strip('"').strip("'")

    bot_data = db.get_bot(token)
    if not bot_data:
        await update.message.reply_text(
            "❌ Bot not found in database.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    context.user_data["clone_source"] = token

    text = f"""
✅ <b>Source selected:</b> @{bot_data.get('username') or 'Unknown'}

Now send me the <b>target</b> bot token (the one to copy TO).
"""

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return STATE_WAITING_CLONE_TARGET


async def receive_clone_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive target token and perform clone"""
    target_token = update.message.text.strip().strip('"').strip("'")
    source_token = context.user_data.get("clone_source")

    if not source_token:
        await update.message.reply_text(
            "❌ Clone session expired. Start over.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    source = db.get_bot(source_token)
    target = db.get_bot(target_token)

    if not target:
        await update.message.reply_text(
            "❌ Target bot not found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    # Clone settings
    db.update_bot_welcome(target_token, source.get("welcome_msg"))
    db.update_bot_buttons(target_token, source.get("buttons_json"))

    await update.message.reply_text(
        f"✅ <b>Clone Complete!</b>\n\n"
        f"Copied settings from @{source.get('username') or 'Unknown'} to @{target.get('username') or 'Unknown'}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )

    context.user_data.pop("clone_source", None)
    return STATE_IDLE


# ============ EDIT WELCOME ============
async def edit_welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt to select bot for welcome edit"""
    query = update.callback_query
    await query.answer()

    bots = db.get_all_bots()
    if not bots:
        await query.edit_message_text(
            "❌ No bots found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    keyboard = []
    for bot in bots:
        username = bot["username"] or "Unknown"
        keyboard.append([InlineKeyboardButton(f"✏️ @{username}", callback_data=f"edit_welcome_bot:{bot['token']}")])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])

    await query.edit_message_text(
        "<b>✏️ Select bot to edit welcome message:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_IDLE


async def edit_welcome_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store selected bot and prompt for new welcome"""
    query = update.callback_query
    await query.answer()

    data = query.data.split(":", 1)
    if len(data) < 2:
        return STATE_IDLE

    token = data[1]
    context.user_data["edit_bot_token"] = token

    bot_data = db.get_bot(token)
    current = bot_data.get("welcome_msg") or "(using default)"

    text = f"""
<b>✏️ Edit Welcome Message</b>

Current message:
<pre>{current[:500]}</pre>

Send me the new welcome message.

<b>Variables:</b>
<code>{{first_name}}</code> - User's first name

<b>Tips:</b>
• Use HTML tags: &lt;b&gt;, &lt;i&gt;, &lt;code&gt;, &lt;pre&gt;
• Use animated emoji: 🎉 🎊 🎈 💖 🔥 ✨
• Users can tap emoji to animate them!
"""

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return STATE_WAITING_WELCOME


async def receive_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new welcome message"""
    token = context.user_data.get("edit_bot_token")
    if not token:
        await update.message.reply_text("❌ Session expired.")
        return STATE_IDLE

    welcome_msg = update.message.text
    db.update_bot_welcome(token, welcome_msg)

    await update.message.reply_text(
        "✅ <b>Welcome message updated!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )

    context.user_data.pop("edit_bot_token", None)
    return STATE_IDLE


# ============ EDIT BUTTONS ============
async def edit_buttons_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt to select bot for button edit"""
    query = update.callback_query
    await query.answer()

    bots = db.get_all_bots()
    if not bots:
        await query.edit_message_text(
            "❌ No bots found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
        return STATE_IDLE

    keyboard = []
    for bot in bots:
        username = bot["username"] or "Unknown"
        keyboard.append([InlineKeyboardButton(f"🔘 @{username}", callback_data=f"edit_buttons_bot:{bot['token']}")])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])

    await query.edit_message_text(
        "<b>🔘 Select bot to edit buttons:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_IDLE


async def edit_buttons_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store selected bot and prompt for button config"""
    query = update.callback_query
    await query.answer()

    data = query.data.split(":", 1)
    if len(data) < 2:
        return STATE_IDLE

    token = data[1]
    context.user_data["edit_buttons_token"] = token

    bot_data = db.get_bot(token)
    current = bot_data.get("buttons_json") or json.dumps(DEFAULT_BUTTONS)

    text = f"""
<b>🔘 Edit Buttons</b>

Current config:
<code>{current}</code>

Send me new button config in JSON format:

<pre>
[
  {{"text": "📢 Channel", "url": "https://t.me/channel"}},
  {{"text": "💬 Chat", "url": "https://t.me/username"}},
  {{"text": "🌐 Website", "url": "https://example.com"}}
]
</pre>

<i>You can add unlimited buttons!</i>
"""

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return STATE_WAITING_BUTTONS


async def receive_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save new button configuration"""
    token = context.user_data.get("edit_buttons_token")
    if not token:
        await update.message.reply_text("❌ Session expired.")
        return STATE_IDLE

    try:
        buttons = json.loads(update.message.text)
        if not isinstance(buttons, list):
            raise ValueError("Must be a list")

        db.update_bot_buttons(token, json.dumps(buttons))

        await update.message.reply_text(
            f"✅ <b>Buttons updated!</b>\n\n"
            f"Total buttons: {len(buttons)}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
            ])
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Invalid JSON:</b> {e}\n\nPlease try again.",
            parse_mode=ParseMode.HTML
        )
        return STATE_WAITING_BUTTONS

    context.user_data.pop("edit_buttons_token", None)
    return STATE_IDLE


# ============ EXPORT TOKENS ============
async def export_tokens_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all tokens to file"""
    query = update.callback_query
    await query.answer("Exporting...")

    filepath = f"/tmp/bot_tokens_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    try:
        db.export_tokens_to_file(filepath)

        # Send file
        with open(filepath, "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                caption=f"📤 <b>Exported {len(db.get_all_bots())} bot tokens</b>",
                parse_mode=ParseMode.HTML
            )

        # Call plugin hook
        await call_hook("on_export", filepath, update.effective_user.id)

        # Clean up
        os.remove(filepath)

        await query.edit_message_text(
            "✅ <b>Export complete!</b> File sent above.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
            ])
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ Export failed: {e}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )

    return STATE_IDLE


# ============ STATS ============
async def show_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    query = update.callback_query
    await query.answer()

    total_bots = len(db.get_all_bots())
    running_bots = len(get_running_bots())
    total_users = db.get_total_users_all_bots()
    unique_users = db.get_user_count()

    text = f"""
{random_premium_header()}

<b>📊 Bot Manager Statistics</b>

🤖 <b>Bots:</b>
   ├ Total: {total_bots}
   ├ Running: {running_bots}
   └ Stopped: {total_bots - running_bots}

👥 <b>Users:</b>
   ├ Total interactions: {total_users}
   └ Unique users: {unique_users}

⚡ <b>System:</b>
   ├ Plugins loaded: {len(get_loaded_plugins())}
   └ Uptime: Active
"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


def get_loaded_plugins():
    from plugins import get_loaded_plugins as gp
    try:
        return gp()
    except:
        return []


# ============ CANCEL / FALLBACK ============
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    await update.message.reply_text(
        "❎ Operation cancelled.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unexpected messages"""
    # Try plugin text hooks first
    try:
        results = await call_hook("on_text_received", update, context)
        if any(results):
            return STATE_IDLE
    except:
        pass

    await update.message.reply_text(
        "⚠️ Please use the buttons or /start to access the panel.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎛️ Open Panel", callback_data="admin_panel")]
        ])
    )
    return STATE_IDLE


# ============ MAIN ============
def main():
    """Start the admin bot"""
    import random

    # Get admin bot token from environment or prompt
    ADMIN_BOT_TOKEN = os.environ.get("ADMIN_BOT_TOKEN")

    if not ADMIN_BOT_TOKEN:
        print("=" * 60)
        print("TELEGRAM BOT MANAGER - SETUP")
        print("=" * 60)
        print("\nPlease set your admin bot token:")
        print("export ADMIN_BOT_TOKEN='your_bot_token_here'")
        print("\nOr create a .env file with ADMIN_BOT_TOKEN")
        print("=" * 60)
        sys.exit(1)

    # Add default admins from config to DB
    for admin_id in ADMIN_IDS:
        db.add_admin(admin_id)

    print("🚀 Starting Telegram Bot Manager...")
    print(f"📊 Database: {db.db_path}")

    # Build application
    app = Application.builder().token(ADMIN_BOT_TOKEN).build()
    global _admin_app
    _admin_app = app

    # Conversation handler for multi-step flows
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"),
            CallbackQueryHandler(add_tokens_callback, pattern="^add_tokens$"),
            CallbackQueryHandler(start_bot_callback, pattern="^start_bot$"),
            CallbackQueryHandler(stop_bot_callback, pattern="^stop_bot$"),
            CallbackQueryHandler(list_bots_callback, pattern="^list_bots$"),
            CallbackQueryHandler(delete_bot_callback, pattern="^delete_bot$"),
            CallbackQueryHandler(broadcast_callback, pattern="^broadcast$"),
            CallbackQueryHandler(check_admin_callback, pattern="^check_admin$"),
            CallbackQueryHandler(clone_bot_callback, pattern="^clone_bot$"),
            CallbackQueryHandler(edit_welcome_callback, pattern="^edit_welcome$"),
            CallbackQueryHandler(edit_buttons_callback, pattern="^edit_buttons$"),
            CallbackQueryHandler(export_tokens_callback, pattern="^export_tokens$"),
            CallbackQueryHandler(show_stats_callback, pattern="^show_stats$"),
            # Action callbacks
            CallbackQueryHandler(do_start_callback, pattern="^do_start:"),
            CallbackQueryHandler(do_stop_callback, pattern="^do_stop:"),
            CallbackQueryHandler(do_delete_callback, pattern="^do_delete:"),
            CallbackQueryHandler(edit_welcome_select_callback, pattern="^edit_welcome_bot:"),
            CallbackQueryHandler(edit_buttons_select_callback, pattern="^edit_buttons_bot:"),
        ],
        states={
            STATE_WAITING_TOKENS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tokens),
            ],
            STATE_WAITING_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast),
            ],
            STATE_WAITING_CHANNEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_check),
            ],
            STATE_WAITING_CLONE_SOURCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_clone_source),
            ],
            STATE_WAITING_CLONE_TARGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_clone_target),
            ],
            STATE_WAITING_WELCOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_welcome),
            ],
            STATE_WAITING_BUTTONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buttons),
            ],
            STATE_IDLE: [
                # In idle state, handle callback queries
                CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"),
                CallbackQueryHandler(add_tokens_callback, pattern="^add_tokens$"),
                CallbackQueryHandler(start_bot_callback, pattern="^start_bot$"),
                CallbackQueryHandler(stop_bot_callback, pattern="^stop_bot$"),
                CallbackQueryHandler(list_bots_callback, pattern="^list_bots$"),
                CallbackQueryHandler(delete_bot_callback, pattern="^delete_bot$"),
                CallbackQueryHandler(broadcast_callback, pattern="^broadcast$"),
                CallbackQueryHandler(check_admin_callback, pattern="^check_admin$"),
                CallbackQueryHandler(clone_bot_callback, pattern="^clone_bot$"),
                CallbackQueryHandler(edit_welcome_callback, pattern="^edit_welcome$"),
                CallbackQueryHandler(edit_buttons_callback, pattern="^edit_buttons$"),
                CallbackQueryHandler(export_tokens_callback, pattern="^export_tokens$"),
                CallbackQueryHandler(show_stats_callback, pattern="^show_stats$"),
                CallbackQueryHandler(do_start_callback, pattern="^do_start:"),
                CallbackQueryHandler(do_stop_callback, pattern="^do_stop:"),
                CallbackQueryHandler(do_delete_callback, pattern="^do_delete:"),
                CallbackQueryHandler(edit_welcome_select_callback, pattern="^edit_welcome_bot:"),
                CallbackQueryHandler(edit_buttons_select_callback, pattern="^edit_buttons_bot:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler),
        ],
        allow_reentry=True
    )

    app.add_handler(conv_handler)

    print("✅ Admin bot initialized")
    print("📱 Send /start to your admin bot to open the panel")
    print("=" * 60)

    # Run
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
