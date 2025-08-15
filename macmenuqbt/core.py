import rumps
from qbittorrentapi import Client
import importlib.metadata
import json
import urllib.request
import argparse
import os
import datetime
import platform
import subprocess
import time
import sys
import ssl
import webbrowser

if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_PATH, "qbt_menu_config.json")
SETTINGS_FILE = os.path.join(BASE_PATH, "qbt_settings.json")

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

DEFAULT_ELEMENTS = [
    {"name": "Status", "state": True},
    {"name": "Progress (%)", "state": True},
    {"name": "DL speed", "state": True},
    {"name": "UP speed", "state": True},
    {"name": "ETA", "state": True},
    {"name": "DL/UP/Tot Size", "state": False},
    {"name": "Ratio UP/DL", "state": False},
    {"name": "Seeds/Leechers", "state": False},
    {"name": "Category", "state": False},
    {"name": "Added on", "state": False},
]

DEFAULT_SETTINGS_FILE_CONTENT = {
    "Launch qBittorrent": 0,
    "Notification": 1,
    "Notification sound": 1,
    "host": "localhost",
    "port": 8080,
    "username": "admin",
    "password": "123456"
}


def check_for_update(package_name="macmenuqbt"):
    try:
        current_version = importlib.metadata.version(package_name)
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package_name}/json", context=context) as response:
            data = json.load(response)
            latest_version = data["info"]["version"]

        if current_version != latest_version:
            return True, f"🎉 A new update is available {current_version} → {latest_version} - Click me"
        return False, current_version

    except Exception as e:
        print(e)
        return None, None


def install_update(_):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "macmenuqbt"])
        rumps.alert("✅ macmenuqbt has been updated.\nPlease restart the app.")
    except Exception as e:
        rumps.alert(f"❌ Update failed:\n{e}")


def launch_qbittorrent():
    system = platform.system()

    if system == "Darwin":
        app_path = "/Applications/qbittorrent.app"
        if os.path.exists(app_path):
            subprocess.Popen(["open", app_path])
            return None
        else:
            return "qBittorrent.app not found in /Applications"
    else:
        return "qBittorrent.app not found in /Applications"


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


class QBitTorrentMenuApp(rumps.App):
    def __init__(self, host, port, username, password, interval=5, qbt=True, credentials=True):
        super().__init__("🌀 qBittorrent")
        self.host, self.port, self.username, self.password, self.interval = host, port, username, password, interval
        self.qbt, self.credentials = qbt, credentials
        self.client, self.is_update, self.msg_version_update = None, None, None
        self.list_torrent = None

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.elements = json.load(f)

            default_names = {e["name"] for e in DEFAULT_ELEMENTS}
            existing_names = {e["name"] for e in self.elements}

            for default_elem in DEFAULT_ELEMENTS:
                if default_elem["name"] not in existing_names:
                    self.elements.append(default_elem)

            self.elements = [e for e in self.elements if e["name"] in default_names]

            with open(CONFIG_FILE, "w") as f:
                json.dump(self.elements, f, indent=2)

        else:
            self.elements = DEFAULT_ELEMENTS.copy()
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.elements, f, indent=2)

        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                self.settings_data = json.load(f)

            for key, value in DEFAULT_SETTINGS_FILE_CONTENT.items():
                if key not in self.settings_data:
                    self.settings_data[key] = value

            self.settings_data = {k: self.settings_data[k] for k in DEFAULT_SETTINGS_FILE_CONTENT.keys()}

        else:
            self.settings_data = DEFAULT_SETTINGS_FILE_CONTENT.copy()

            self.settings_data["host"] = host
            self.settings_data["port"] = port
            self.settings_data["username"] = username
            self.settings_data["password"] = password

            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings_data, f, indent=2)

        if self.settings_data['Launch qBittorrent']:
            launch_qbittorrent()
            time.sleep(2)

        self.connected, self.msg_connection = self.connect_to_qbittorrent()

        if self.connected:
            self.list_torrent = self.client.torrents_info()

        self.menu.clear()
        self.build_menu()
        self.timer = rumps.Timer(self.update_menu, self.interval)
        self.timer.start()

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.elements, f, indent=2)

    def move_element(self, idx, delta, absolute=False):
        if absolute:
            if delta < 0:
                while idx > 0:
                    self.elements[idx], self.elements[idx - 1] = self.elements[idx - 1], self.elements[idx]
                    idx -= 1
            else:
                while idx < len(self.elements) - 1:
                    self.elements[idx], self.elements[idx + 1] = self.elements[idx + 1], self.elements[idx]
                    idx += 1
        else:
            new_idx = idx + delta
            if 0 <= new_idx < len(self.elements):
                self.elements[idx], self.elements[new_idx] = self.elements[new_idx], self.elements[idx]

        self.build_menu()
        self.save_config()

    def build_menu(self):
        for idx, elem in enumerate(self.elements):
            item = rumps.MenuItem(elem["name"], callback=self.toggle_element)
            item.state = elem["state"]

            move_top = rumps.MenuItem("↑↑ Move Top",
                                      callback=lambda sender, i=idx: self.move_element(i, -1, absolute=True))
            move_up = rumps.MenuItem("↑ Move Up", callback=lambda sender, i=idx: self.move_element(i, -1))
            move_down = rumps.MenuItem("↓ Move Down", callback=lambda sender, i=idx: self.move_element(i, 1))
            move_bottom = rumps.MenuItem("↓↓ Move Bottom",
                                         callback=lambda sender, i=idx: self.move_element(i, 1, absolute=True))

            item.add(move_top)
            item.add(move_up)
            item.add(move_down)
            item.add(move_bottom)

            if elem["name"] == "Status":
                help_status = rumps.MenuItem("Helps")

                for status, emoji in STATUS_ICONS.items():
                    if status == "all":
                        continue
                    item_name = f"{status.capitalize()} {emoji}"
                    help_status.add(rumps.MenuItem(item_name, callback=None))

                help_status.add(rumps.MenuItem("Unknown ❓", callback=None))

                item.add(help_status)

            self.menu.add(item)

        self.menu.add(None)
        self.menu.add(rumps.MenuItem("All ON/OFF", callback=self.toggle_all))
        self.menu.add(None)

        if self.qbt is True:
            launch_item = rumps.MenuItem("Launch qBittorrent", callback=self.toggle_launch_qbt)
            launch_item.state = self.settings_data["Launch qBittorrent"]
            self.menu.add(launch_item)

        notification = rumps.MenuItem("Notification", callback=self.toggle_notification)
        notification.state = self.settings_data["Notification"]
        notification_sound = rumps.MenuItem("Notification sound", callback=self.toggle_notification_sound)
        notification_sound.state = self.settings_data["Notification sound"]
        notification.add(notification_sound)
        self.menu.add(notification)

        if self.credentials is True:
            self.menu.add(rumps.MenuItem("Credentials login", callback=self.open_qbt_settings))

        self.menu.add(None)
        if self.is_update is False:
            self.menu.add(f"v{self.msg_version_update}")

        self.menu.add(None)
        self.menu.add(rumps.MenuItem("Made with ❤️ by Minniti Julien", callback=self.open_github))

        self.menu.add(None)
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    def toggle_element(self, sender):
        for elem in self.elements:
            if elem["name"] == sender.title:
                elem["state"] = not elem["state"]
                sender.state = elem["state"]
                break
        self.save_config()

    def toggle_all(self, sender):
        new_state = not all(e["state"] for e in self.elements)
        for elem in self.elements:
            elem["state"] = new_state
        self.build_menu()
        self.save_config()

    def toggle_launch_qbt(self, sender):
        sender.state = not sender.state
        self.settings_data["Launch qBittorrent"] = sender.state
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings_data, f, indent=2)
        if sender.state:
            launch_qbittorrent()

    def toggle_notification(self, sender):
        sender.state = not sender.state
        self.settings_data["Notification"] = sender.state
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings_data, f, indent=2)

    def toggle_notification_sound(self, sender):
        sender.state = not sender.state
        self.settings_data["Notification sound"] = sender.state
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings_data, f, indent=2)

    def connect_to_qbittorrent(self):
        try:
            self.client = Client(host=self.settings_data['host'], port=self.settings_data['port'],
                                 username=self.settings_data['username'], password=self.settings_data['password'])
            self.client.auth_log_in()
            return True, None
        except Exception as e:
            return False, f"Failed to connect: {e}"

    def open_qbt_settings(self, sender):
        if not os.path.exists(SETTINGS_FILE):
            rumps.alert("Settings file not found.")
            return

        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)

        default_text = (
            f"Host: {settings.get('host', 'localhost')}\n"
            f"Port: {settings.get('port', 8080)}\n"
            f"Username: {settings.get('username', 'admin')}\n"
            f"Password: {settings.get('password', '')}"
        )

        window = rumps.Window(
            title="qBittorrent Settings",
            message="Edit your qBittorrent Web UI credentials",
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 200),
            default_text=default_text
        )

        response = window.run()

        if response.clicked:
            try:
                lines = response.text.splitlines()
                settings.update({
                    "host": lines[0].split(":", 1)[1].strip(),
                    "port": int(lines[1].split(":", 1)[1].strip()),
                    "username": lines[2].split(":", 1)[1].strip(),
                    "password": lines[3].split(":", 1)[1].strip()
                })

                with open(SETTINGS_FILE, "w") as f:
                    json.dump(settings, f, indent=2)

                with open(SETTINGS_FILE, "r") as f:
                    self.settings_data = json.load(f)

                self.connected, _ = self.connect_to_qbittorrent()

                rumps.alert("Settings saved!")
            except Exception as e:
                rumps.alert(f"Error saving settings:\n{e}")

    @staticmethod
    def open_github(self):
        webbrowser.open("https://github.com/Jumitti/MacMenu-qBittorrent")

    @rumps.timer(1)
    def update_menu(self, _=None):
        if not self.client.is_logged_in:
            self.title = "⚠️ qBittorrent"
            self.menu.clear()
            self.menu.add("⚠️ Connection qBittorrent lost")
            self.menu.add("Start qBittorrent or verify your login credentials")
            self.menu.add(None)
            self.build_menu()
            with open(SETTINGS_FILE, "r") as f:
                self.settings_data = json.load(f)
            self.connect_to_qbittorrent()
        else:
            try:
                torrents = self.client.torrents_info()
                current_torrents = {t.hash: t for t in torrents}
                if self.list_torrent is None:
                    previous_torrents = current_torrents
                else:
                    previous_torrents = {t.hash: t for t in self.list_torrent}

                for hash_, old_t in previous_torrents.items():
                    if hash_ not in current_torrents:
                        if self.settings_data['Notification']:
                            rumps.notification(
                                "🎉 Torrent finished !",
                                subtitle=None,
                                message=old_t.name,
                                sound=self.settings_data['Notification sound']
                            )

                self.list_torrent = torrents

                self.menu.clear()
                if not torrents:
                    self.title = "🌀 qBittorrent"
                    self.menu.add("⚪ No torrent found")
                    self.menu.add(None)
                else:
                    total_progress = sum(t.progress for t in torrents) / len(torrents)
                    self.title = f"🌀 qBittorrent {total_progress * 100:.1f}%"

                    for t in torrents:
                        parts = [t.name]
                        for elem in self.elements:
                            if not elem["state"]:
                                continue
                            if elem["name"] == "Status":
                                status_icon = STATUS_ICONS.get(t.state, "❓")
                                parts.append(f"{status_icon}")

                            elif elem["name"] == "DL/UP/Tot Size":
                                total_size = t.size / 1024 ** 3
                                downloaded_size = t.downloaded / 1024 ** 3
                                uploaded_size = t.uploaded / 1024 ** 3
                                parts.append(
                                    f"📥 {t.downloaded / 1024 ** 3:.2f} / 📤{t.uploaded / 1024 ** 3:.2f} / 📦{t.size / 1024 ** 3:.2f} Go")

                            elif elem["name"] == "Progress (%)":
                                parts.append(f"🏃🏽{t.progress * 100:.1f}%")

                            elif elem["name"] == "Ratio UP/DL":
                                parts.append(f"📊 {t.ratio * 100:.1f}%")

                            elif elem["name"] == "DL speed":
                                parts.append(f"⬇️ {format_speed(t.dlspeed)}")

                            elif elem["name"] == "UP speed":
                                parts.append(f"⬆️ {format_speed(t.upspeed)}")

                            elif elem["name"] == "ETA":
                                parts.append(f"⏳ {format_eta(t.eta)}")

                            elif elem["name"] == "Seeds/Leechers":
                                parts.append(f"🌱{t.num_seeds}/🧲{t.num_leechs}")

                            elif elem["name"] == "Category":
                                parts.append(f"🏷️ {t.category}")

                            elif elem["name"] == "Added on":
                                dt = datetime.datetime.fromtimestamp(t.added_on)
                                parts.append(f"📆 {dt.strftime('%Y-%m-%d %H:%M')}")
                        self.menu.add(" | ".join(parts))

                self.build_menu()
                self.menu.add(None)
                self.is_update, self.msg_version_update = check_for_update()
                if self.is_update:
                    version = rumps.MenuItem(self.msg_version_update, callback=install_update)
                    self.menu.add(version)

            except Exception as e:
                self.menu.clear()
                self.menu.add(f"⚠️ Error: {str(e)}")
                self.build_menu()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="qBittorrent macOS Menu Bar App")
    parser.add_argument("-H", "--host", default="localhost")
    parser.add_argument("-P", "--port", type=int, default=8080)
    parser.add_argument("-U", "--username", default="admin")
    parser.add_argument("-PSW", "--password", default="123456")
    parser.add_argument("-I", "--interval", type=int, default=5)
    try:
        version = importlib.metadata.version("macmenuqbt")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    parser.add_argument("-V", "--version", action="version", version=f"MacMenu-qBittorrent {version}")
    return parser.parse_args(argv)


def main(host=None, port=None, username=None, password=None, interval=None, qbt=True, credentials=True):
    if all(arg is None for arg in [host, port, username, password, interval]):
        args = parse_args()
        host, port, username, password, interval = args.host, args.port, args.username, args.password, args.interval

    app = QBitTorrentMenuApp(host, port, username, password, interval, qbt, credentials)
    app.run()


if __name__ == "__main__":
    main()
