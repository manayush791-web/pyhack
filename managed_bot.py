"""
Managed Bot Handler
Each added bot token gets its own Application instance running concurrently.
This module handles the /start and welcome message logic for all managed bots.
"""
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from config import DEFAULT_WELCOME_MSG, DEFAULT_BUTTONS, PREMIUM_EMOJI
from database import db
from plugins import call_hook

# Active managed bot applications
_running_bots = {}


def get_premium_decorations():
    """Generate premium visual decorations using animated emoji"""
    header_emoji = random.choice(["✨", "🌟", "💎", "👑", "🎉", "🔥"])
    footer_emoji = random.choice(["💖", "🎊", "🎈", "💫", "🌈", "⚡"])
    return header_emoji, footer_emoji


def build_welcome_keyboard(buttons_json=None, extra_buttons=None):
    """Build inline keyboard from stored buttons + extras"""
    keyboard = []

    # Parse stored buttons
    if buttons_json:
        try:
            stored = json.loads(buttons_json)
            for btn in stored:
                if btn.get("url"):
                    keyboard.append([InlineKeyboardButton(btn["text"], url=btn["url"])])
        except:
            pass

    # Default fallback
    if not keyboard:
        for btn in DEFAULT_BUTTONS:
            keyboard.append([InlineKeyboardButton(btn["text"], url=btn["url"])])

    # Add extra dynamic buttons if provided
    if extra_buttons:
        for btn in extra_buttons:
            if btn.get("url"):
                keyboard.append([InlineKeyboardButton(btn["text"], url=btn["url"])])
            elif btn.get("callback_data"):
                keyboard.append([InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"])])

    return InlineKeyboardMarkup(keyboard)


def format_premium_welcome(first_name, custom_msg=None):
    """Format welcome message with premium styling and animated emoji"""
    header, footer = get_premium_decorations()

    # Use custom message if available, else default
    if custom_msg:
        msg = custom_msg.replace("{first_name}", first_name)
    else:
        msg = DEFAULT_WELCOME_MSG.replace("{first_name}", first_name)

    # Add premium header/footer if not already styled
    if not msg.startswith("<"):
        msg = f"{header} <b>Premium Experience</b> {header}\n\n{msg}"

    if "Tap any emoji" not in msg:
        msg += f"\n\n{footer} <i>Tap any emoji above to see it animate!</i> {footer}"

    # Inject some random premium emoji for visual appeal
    premium_line = "\n".join([
        "🎉 🎊 🎈 🎁 🎄 🎃 🕯 💖 ❤️‍🔥 👍 🐳 🌟 ⚡ 🔥 💫 ✨ 🌈 ☄️",
        "💎 🏆 🥇 🎯 🎰 🎲 🎮 🕹️ 🎸 🎺 🎻 🎹 🥁 🎤 🎧 🎷 🎼 🎵 🎶"
    ])

    if "🎉" not in msg:
        msg += f"\n\n<tg-spoiler>{premium_line}</tg-spoiler>"

    return msg


async def managed_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start for managed bots - PREMIUM WELCOME"""
    user = update.effective_user
    chat = update.effective_chat
    bot_token = context.bot.token

    # Track user in database
    is_new = db.add_user(
        user_id=user.id,
        bot_token=bot_token,
        first_name=user.first_name or "User",
        username=user.username or "",
        chat_id=chat.id
    )

    # Call plugin hook
    await call_hook("on_user_joined", user.id, bot_token)

    # Get bot-specific settings
    bot_data = db.get_bot(bot_token)
    custom_msg = bot_data.get("welcome_msg") if bot_data else None
    buttons_json = bot_data.get("buttons_json") if bot_data else None

    # Build welcome message
    welcome_text = format_premium_welcome(user.first_name or "Friend", custom_msg)

    # Build keyboard
    reply_markup = build_welcome_keyboard(buttons_json)

    # Send premium welcome with HTML parse mode
    try:
        await update.message.reply_text(
            text=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

        # Send a follow-up animated sticker or dice for extra premium feel
        if is_new:
            # Send a dice animation (reacts to touch/roll)
            await context.bot.send_dice(
                chat_id=chat.id,
                emoji="🎉"  # Other options: 🎲, 🎯, 🏀, ⚽, 🎳, 🎰
            )

            # Send a premium animated sticker (if available) - using a popular animated sticker
            # Note: In production, replace with your own sticker set file_id
            # This is a placeholder for the concept

    except Exception as e:
        print(f"[ManagedBot] Error sending welcome: {e}")
        await update.message.reply_text(
            "Welcome! 🎉",
            parse_mode=ParseMode.HTML
        )


async def managed_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help for managed bots"""
    help_text = """
<b>🎉 Available Commands:</b>

/start - Start the bot & see welcome message
/help - Show this help message

<i>Tap any emoji to see it animate! ✨</i>
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def create_managed_bot_app(token, welcome_msg=None, buttons_json=None):
    """Create and configure a new managed bot Application"""
    app = Application.builder().token(token).build()

    # Add handlers
    app.add_handler(CommandHandler("start", managed_start_handler))
    app.add_handler(CommandHandler("help", managed_help_handler))

    # Store bot data in bot_data for handlers to access
    app.bot_data["welcome_msg"] = welcome_msg
    app.bot_data["buttons_json"] = buttons_json

    return app


async def start_managed_bot(token):
    """Start a managed bot application"""
    if token in _running_bots:
        return False, "Bot already running"

    bot_data = db.get_bot(token)
    if not bot_data:
        return False, "Bot not found in database"

    try:
        app = await create_managed_bot_app(
            token,
            welcome_msg=bot_data.get("welcome_msg"),
            buttons_json=bot_data.get("buttons_json")
        )

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        # Get bot info
        me = await app.bot.get_me()

        _running_bots[token] = {
            "app": app,
            "bot": app.bot,
            "username": me.username,
            "id": me.id
        }

        db.update_bot_status(token, "running")
        await call_hook("on_bot_started", token, me.username)

        return True, me.username
    except Exception as e:
        return False, str(e)


async def stop_managed_bot(token):
    """Stop a managed bot application"""
    if token not in _running_bots:
        return False, "Bot not running"

    try:
        bot_info = _running_bots[token]
        app = bot_info["app"]
        username = bot_info["username"]

        await app.updater.stop()
        await app.stop()
        await app.shutdown()

        del _running_bots[token]
        db.update_bot_status(token, "stopped")
        await call_hook("on_bot_stopped", token, username)

        return True, username
    except Exception as e:
        return False, str(e)


async def stop_all_managed_bots():
    """Stop all running managed bots"""
    tokens = list(_running_bots.keys())
    for token in tokens:
        await stop_managed_bot(token)


def get_running_bots():
    """Get list of currently running managed bots"""
    return {
        token: {"username": info["username"], "id": info["id"]}
        for token, info in _running_bots.items()
    }


def is_bot_running(token):
    return token in _running_bots
