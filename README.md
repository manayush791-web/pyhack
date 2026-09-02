# 🤖 Telegram Bot Manager

A premium, multi-bot management system built with `python-telegram-bot` v20+. Host unlimited Telegram bots from a single admin panel with animated emoji, broadcast capabilities, and a plugin architecture.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| ➕ **Multi-Token Input** | Add many bot tokens at once, line by line, with or without quotes |
| 🚀 **Start/Stop Bots** | Launch and stop managed bots individually |
| 📢 **Global Broadcast** | Send messages to ALL users who ever started ANY of your bots |
| 👮 **Admin Checker** | Verify if your bots are admin in any group/channel |
| 🔄 **Bot Cloner** | Copy welcome message & button settings between bots |
| ✏️ **Custom Welcome** | Edit welcome messages per bot with HTML & animated emoji |
| 🔘 **Dynamic Buttons** | Add unlimited custom buttons (URL or callback) per bot |
| 📤 **Export Tokens** | Export all stored tokens to a file in one click |
| 📊 **Statistics** | View total bots, users, and system stats |
| 🔌 **Plugin System** | Add new features without touching core code |

---

## 🎉 Premium Welcome Experience

Every managed bot sends a **visually stunning welcome message** featuring:
- 🎊 **Animated emoji** that react to touch (tap to animate!)
- 💎 **Premium HTML styling** with borders, spoilers, and formatting
- 🎲 **Interactive dice/animations** sent automatically
- 🔘 **Custom inline buttons** for channel, chat, and more
- 🌈 **Randomized visual themes** on every greeting

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Admin
Edit `config.py` and set your Telegram User ID:
```python
ADMIN_IDS = [
    123456789,  # Replace with your ID (get from @userinfobot)
]
```

### 3. Set Admin Bot Token
```bash
export ADMIN_BOT_TOKEN="123456:ABC-DEF..."
```

Or create a `.env` file:
```
ADMIN_BOT_TOKEN=123456:ABC-DEF...
```

### 4. Run
```bash
python main.py
```

### 5. Open Panel
Send `/start` to your admin bot. You'll see the control panel with all buttons.

---

## 📋 Usage Guide

### Adding Bot Tokens
Send tokens in any format:
```
123456789:ABCdefGHIjklMNOpqrSTUvwxyz
"987654321:XYZabcDEFghiJKLmnoPQRstu"
'456789123:LMNopqRSTuvwXYZabcDEFghi'
```

### Starting a Bot
1. Press **🚀 Start Bot**
2. Select from your stored tokens
3. Bot goes live instantly!

### Broadcasting
1. Press **📢 Broadcast**
2. Type your message (supports HTML)
3. It reaches **every user** across **all bots**

### Customizing Welcome
1. Press **✏️ Edit Welcome**
2. Select a bot
3. Send new message with `{{first_name}}` variable

### Customizing Buttons
1. Press **🔘 Edit Buttons**
2. Select a bot
3. Send JSON like:
```json
[
  {"text": "📢 Channel", "url": "https://t.me/channel"},
  {"text": "💬 Support", "url": "https://t.me/username"}
]
```

---

## 🔌 Plugin System

Add features **without changing core code**!

### Creating a Plugin

1. Create a new file in `plugins/` folder, e.g., `plugins/my_feature.py`:

```python
from plugins import register_hook
from telegram import InlineKeyboardButton

@register_hook("on_admin_panel")
async def add_my_button(keyboard, context):
    keyboard.append([
        InlineKeyboardButton("🎮 My Feature", callback_data="my_feature")
    ])
    return keyboard

@register_hook("on_bot_added")
async def log_new_bot(token, username):
    print(f"New bot added: @{username}")
```

2. Restart the bot — your plugin loads automatically!

### Available Hooks

| Hook | Trigger | Args |
|------|---------|------|
| `on_bot_added` | New token stored | `(token, username)` |
| `on_bot_started` | Bot goes live | `(token, username)` |
| `on_bot_stopped` | Bot stopped | `(token, username)` |
| `on_broadcast_sent` | Broadcast done | `(token_or_all, count)` |
| `on_admin_panel` | Panel rendered | `(keyboard, context)` |
| `on_export` | Tokens exported | `(filepath, admin_id)` |
| `on_user_joined` | User starts bot | `(user_id, bot_token)` |
| `on_text_received` | Any text msg | `(update, context)` → return `True` to block |

---

## 🏗️ Project Structure

```
telegram_bot_manager/
├── main.py                  # Admin bot & orchestrator
├── managed_bot.py           # Managed bot handlers
├── database.py              # SQLite operations
├── config.py                # Settings & defaults
├── requirements.txt         # Dependencies
├── plugins/
│   ├── __init__.py          # Plugin loader & hooks
│   └── export_tokens.py     # Export feature (example)
└── bot_manager.db           # Auto-created SQLite DB
```

---

## 🎨 Premium Emoji Reference

The following emoji animate when tapped in Telegram clients:

**Celebration:** 🎉 🎊 🎈 🎁 🎄 🎃 🕯 🎆 🎇 🧨 🍾 🥂  
**Love:** 💖 ❤️‍🔥 💝 💘 💗 💓 💞 💕 💌 🖤 🤍  
**Power:** 🌟 ⚡ 🔥 💫 ✨ 🌈 ☄️ 💎 🏆 🥇 🎯  
**Fun:** 🐳 🎰 🎲 🎮 🕹️ 🎸 🎺 🎻 🎹 🥁 🎤 🎧 🎷 🎼 🎵 🎶  
**People:** 🧚 🧜 🧝 🧙 🧛 🧟 🧞 🦸 🦹 🧑‍🎤 🧑‍🚀 🧑‍⚖️ 🧑‍✈️  
**Professions:** 🧑‍🌾 🧑‍🍳 🧑‍🔧 🧑‍🏭 🧑‍💼 🧑‍🔬 🧑‍💻 🧑‍🎨 🧑‍🚒 🧑‍⚕️ 🧑‍🎓 🧑‍🏫  

Use these in welcome messages for the best premium feel!

---

## ⚠️ Notes

- **Admin Bot**: This is Bot A. You control everything through it.
- **Managed Bots**: These are Bot B, C, D... They welcome users independently.
- **Database**: All data is stored locally in `bot_manager.db`.
- **Broadcast**: Sends to every user who ever `/start`ed any managed bot.
- **Touch-to-Animate**: Emoji animation is handled by the Telegram client. Premium users see automatic animation; all users can tap to animate.

---

## 📜 License

MIT License — Use freely, modify boldly, share widely.

---

Made with 💖, 🔥, and ✨ by the Bot Manager System.
