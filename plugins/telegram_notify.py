import asyncio
import datetime
import json
import os
import threading

import rumps
from telegram import Bot
from telegram.ext import Application, CommandHandler

PLUGIN_NAME = "telegram_notify"
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), f"{PLUGIN_NAME}_settings.json")

DEFAULT_SETTINGS = {
    "token": "",
    "chat_id": ""
}

STATUS_ICONS = {
    "downloading": "⬇️",
    "resumed": "⬇️",
    "running": "⬇️",
    "forcedDL": "⬇️",
    "seeding": "🌱",
    "completed": "✅",
    "paused": "⏸️",
    "stopped": "⏸️",
    "inactive": "⏸️",
    "active": "🔄",
    "stalled": "⚠️",
    "stalled_uploading": "⚠️",
    "stalled_downloading": "⚠️",
    "checking": "🔍",
    "moving": "📦",
    "errored": "❌",
    "all": "📋"
}


def start_telegram_listener(app):
    settings_data = load_settings()
    token = settings_data.get("token")
    chat_id = settings_data.get("chat_id")

    def format_speed(speed_bytes_per_s):
        kb_s = speed_bytes_per_s / 1024
        if kb_s >= 500:
            mb_s = kb_s / 1024
            return f"{mb_s:.2f} Mo/s"
        else:
            return f"{kb_s:.1f} Ko/s"

    def format_eta(seconds):
        if seconds < 0:
            return "∞"
        return str(datetime.timedelta(seconds=seconds))

    if not token or not chat_id:
        rumps.alert("❌ Error sending message. Please check credentials")
        return

    async def list_command(update, context):
        if str(update.effective_chat.id) != str(chat_id):
            return

        torrents_text = []
        for t in app.current_torrents.values():
            parts = [f"📂 {t.name}"]

            status_icon = STATUS_ICONS.get(t.state, "❓")
            parts.append(f"{status_icon}")

            parts.append(f"🏃🏽 {t.progress * 100:.1f}%")

            parts.append(f"⬇️ {format_speed(t.dlspeed)} ⬆️ {format_speed(t.upspeed)}")

            total_size = t.size / 1024 ** 3
            downloaded_size = t.downloaded / 1024 ** 3
            uploaded_size = t.uploaded / 1024 ** 3
            parts.append(
                f"📥 {t.downloaded / 1024 ** 3:.2f} / 📤{t.uploaded / 1024 ** 3:.2f} / 📦{t.size / 1024 ** 3:.2f} Go")

            parts.append(f"📊 Ratio {t.ratio:.2f}")

            parts.append(f"🌱{t.num_seeds}/🧲{t.num_leechs}")

            parts.append(f"⏳ {format_eta(t.eta)}")

            parts.append(f"🏷️ {t.category}")

            dt = datetime.datetime.fromtimestamp(t.added_on)
            parts.append(f"📆 {dt.strftime('%Y-%m-%d %H:%M')}")

            torrents_text.append(" | ".join(parts))

        if not torrents_text:
            msg = "📭 No torrents currently running."
        else:
            msg = "\n\n".join(torrents_text)

        await context.bot.send_message(chat_id=chat_id, text=msg)

    def start_bot():
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        application = Application.builder().token(token).build()
        application.add_handler(CommandHandler("list", list_command))

        application.run_polling(stop_signals=None)

    def run_in_thread():
        import asyncio
        asyncio.run(start_bot())

    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def send_telegram_message(token, chat_id, text):
    async def _send():
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=text)

    try:
        asyncio.run(_send())
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def settings(app, plugin_menu):
    def test_message():
        settings_data = load_settings()
        msg_response = "I'm running 🏃🏽"

        success = send_telegram_message(
            settings_data["token"],
            settings_data["chat_id"],
            msg_response
        )
        if success:
            pass
        else:
            rumps.alert("❌ Error sending message. Please check credentials")

    def credentials(_):
        settings_data = load_settings()

        response = rumps.Window(
            message="Enter your Token and Chat ID",
            title="Configuration Telegram",
            default_text=f"Token: {settings_data['token']}\nChat ID: {settings_data['chat_id']}",
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 60),
        ).run()

        if response.clicked:
            lines = response.text.strip().splitlines()
            if len(lines) >= 2:
                token = lines[0].replace("Token:", "").strip()
                chat_id = lines[1].replace("Chat ID:", "").strip()

                settings_data["token"] = token
                settings_data["chat_id"] = chat_id
                save_settings(settings_data)
                rumps.alert("✅ Telegram configuration saved")
            else:
                rumps.alert("⚠️ You must enter a Token AND a Chat ID.")

        settings_data = load_settings()

        test_message()

    plugin_menu.add(rumps.MenuItem("Credentials", callback=credentials))

    def send_message(_):
        settings_data = load_settings()

        if not settings_data["token"] or not settings_data["chat_id"]:
            rumps.alert("⚠️ First, configure the Telegram bot in 'Credentials'.")
            return

        msg_response = "I'm running 🏃🏽"

        test_message()

    plugin_menu.add(rumps.MenuItem("Send test message", callback=send_message))


def run(app):
    settings_data = load_settings()

    for hash_, old_t in app.previous_torrents.items():
        if hash_ not in app.current_torrents:
            msg = "🎉 Torrent finished ! " + old_t.name
            success = send_telegram_message(
                settings_data["token"],
                settings_data["chat_id"],
                msg
            )

    if not getattr(app, "_telegram_listener_started", False):
        start_telegram_listener(app)
        app._telegram_listener_started = True
