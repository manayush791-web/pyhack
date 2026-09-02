"""
Configuration for Telegram Bot Manager
"""
import os

# ============ ADMIN CONFIG ============
# Add your Telegram User ID here (get it from @userinfobot)
ADMIN_IDS = [
    8725194109,
    8023793790,  # Replace with your Telegram user ID
]

# ============ DATABASE ============
DB_PATH = os.path.join(os.path.dirname(__file__), "bot_manager.db")

# ============ MANAGED BOT DEFAULTS ============
DEFAULT_WELCOME_MSG = """
<blockquote expandable>✨ <b>Welcome to the Premium Experience</b> ✨</blockquote>

🎉 <b>Hello {first_name}!</b> 🎉

💖 <i>We're thrilled to have you here!</i> 💖

🌟 <b>What makes us special:</b>
🔥 Premium animated content
⚡ Lightning-fast updates  
💎 Exclusive member benefits
🎊 Tap any emoji to see it come alive!

🎈 <b>Enjoy your stay and explore!</b> 🎈

<tg-spoiler>🎁 Secret: Tap the buttons below!</tg-spoiler>
""".strip()

# Premium animated emoji that react to touch in Telegram clients
PREMIUM_EMOJI = [
    "🎉", "🎊", "🎈", "🎁", "🎄", "🎃", "🕯", "💖", "❤️‍🔥", "👍",
    "🐳", "🌟", "⚡", "🔥", "💫", "✨", "🌈", "☄️", "🍾", "🥂",
    "🎆", "🎇", "🧨", "💎", "🏆", "🥇", "🎯", "🎰", "🎲", "🎮",
    "🕹️", "🎸", "🎺", "🎻", "🎹", "🥁", "🎤", "🎧", "🎷", "🎼",
    "🎵", "🎶", "🎙️", "🖤", "🤍", "💝", "💘", "💗", "💓", "💞",
    "💕", "💌", "🫀", "🫁", "🧠", "🦷", "🦴", "👀", "👁️", "🧚",
    "🧜", "🧝", "🧙", "🧛", "🧟", "🧞", "🦸", "🦹", "🧑‍🎤", "🧑‍🚀",
    "🧑‍⚖️", "🧑‍✈️", "🧑‍🌾", "🧑‍🍳", "🧑‍🔧", "🧑‍🏭", "🧑‍💼", "🧑‍🔬",
    "🧑‍💻", "🧑‍🎨", "🧑‍🚒", "🧑‍⚕️", "🧑‍🎓", "🧑‍🏫"
]

# Default buttons for managed bots
DEFAULT_BUTTONS = [
    {"text": "📢 Join Our Channel", "url": "https://t.me/father_ddos"},
    {"text": "💬 Contact Support", "url": "https://t.me/dev_ker"}
]

# ============ STATES ============
(STATE_IDLE, STATE_WAITING_TOKENS, STATE_WAITING_BROADCAST, 
 STATE_WAITING_WELCOME, STATE_WAITING_BUTTONS, STATE_WAITING_CHANNEL,
 STATE_WAITING_CLONE_SOURCE, STATE_WAITING_CLONE_TARGET) = range(8)
