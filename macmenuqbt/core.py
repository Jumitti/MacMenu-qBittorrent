import rumps
from qbittorrentapi import Client
import importlib.metadata
import json
import urllib.request
import datetime
import argparse
import os
import datetime

CONFIG_FILE = "qbt_menu_config.json"

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


def check_for_update(package_name="macmenuqbt"):
    try:
        current_version = importlib.metadata.version(package_name)
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package_name}/json") as response:
            data = json.load(response)
            latest_version = data["info"]["version"]

        if current_version != latest_version:
            return f"A new version of {package_name} is available: {latest_version} (you have {current_version})"

    except Exception as e:
        pass


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
    def __init__(self, host, port, username, password, interval=5):
        super().__init__("🌀 qBittorrent")
        self.host, self.port, self.username, self.password, self.interval = host, port, username, password, interval
        self.client = None

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

        self.menu.clear()
        self.build_menu()
        self.timer = rumps.Timer(self.update_menu, self.interval)
        self.timer.start()

        self.connect_to_qbittorrent()

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

    def connect_to_qbittorrent(self):
        self.client = Client(host=self.host, port=self.port, username=self.username, password=self.password)
        try:
            self.client.auth_log_in()
            print("Connected to qBittorrent Web UI")
        except Exception as e:
            print(f"Failed to connect: {e}")

    @rumps.timer(1)
    def update_menu(self, _=None):
        try:
            torrents = self.client.torrents_info()
            self.menu.clear()
            if not torrents:
                self.title = "🌀 qBittorrent"
                self.menu.add("⚪ No torrent found")
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
                            parts.append(f"📥 {t.downloaded / 1024 ** 3:.2f} / 📤{t.uploaded / 1024 ** 3:.2f} / 📦{t.size / 1024 ** 3:.2f} Go")

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
            self.menu.add(check_for_update())

        except Exception as e:
            self.title = "⚠️ Error"
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


def main(host=None, port=None, username=None, password=None, interval=None):
    if all(arg is None for arg in [host, port, username, password, interval]):
        args = parse_args()
        host, port, username, password, interval = args.host, args.port, args.username, args.password, args.interval
    app = QBitTorrentMenuApp(host, port, username, password, interval)
    app.run()


if __name__ == "__main__":
    main()
