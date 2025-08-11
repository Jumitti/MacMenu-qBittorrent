import argparse
import rumps
from qbittorrentapi import Client
import importlib.metadata
import importlib.metadata
import json
import urllib.request

import rumps
from qbittorrentapi import Client


def check_for_update(package_name="macmenuqbt"):
    try:
        current_version = importlib.metadata.version(package_name)

        with urllib.request.urlopen(f"https://pypi.org/pypi/{package_name}/json") as response:
            data = json.load(response)
            latest_version = data["info"]["version"]

        if current_version != latest_version:
            print(f"[yellow]A new version of {package_name} is available: {latest_version} (you have {current_version})[/yellow]")
            print(f"[yellow]Run 'pip install --upgrade {package_name}' to update.[/yellow]")
    except Exception:
        pass


class QBitTorrentMenuApp(rumps.App):
    def __init__(self, host, port, username, password, interval=5):
        super().__init__("qBittorrent")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.interval = interval

        self.client = None
        self.menu.clear()
        self.timer = rumps.Timer(self.update_menu, self.interval)
        self.timer.start()

        self.connect_to_qbittorrent()

    def connect_to_qbittorrent(self):
        self.client = Client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        try:
            self.client.auth_log_in()
            print("Connected to qBittorrent Web UI")
        except Exception as e:
            print(f"Failed to connect: {e}")

    @rumps.timer(5)
    def update_menu(self, _=None):
        try:
            torrents = self.client.torrents_info()
            self.menu.clear()
            if not torrents:
                self.menu.add("No torrents found")
                return

            for t in torrents:
                progress = f"{t.progress * 100:.1f}%"
                title = f"{t.name} — {progress}"
                self.menu.add(title)
        except Exception as e:
            self.menu.clear()
            self.menu.add(f"Error: {str(e)}")
            try:
                self.client.auth_log_in()
            except:
                pass


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="qBittorrent macOS Menu Bar App")

    parser.add_argument("-H", "--host", default="localhost", help="qBittorrent Web UI host")
    parser.add_argument("-P", "--port", type=int, default=8080, help="qBittorrent Web UI port")
    parser.add_argument("-U", "--username", default="admin", help="qBittorrent Web UI username")
    parser.add_argument("-PSW", "--password", default="123456", help="qBittorrent Web UI password")
    parser.add_argument("-I", "--interval", type=int, default=5, help="Update interval in seconds (default 5)")

    try:
        version = importlib.metadata.version("macmenuqbt")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"MacMenu-qBittorrent {version}",
        help="Show program version and exit"
    )

    return parser.parse_args(argv)


def main(host=None, port=None, username=None, password=None, interval=None):
    check_for_update()
    if all(arg is None for arg in [host, port, username, password, interval]):
        # Mode CLI
        args = parse_args()
        host = args.host
        port = args.port
        username = args.username
        password = args.password
        interval = args.interval

    app = QBitTorrentMenuApp(
        host=host,
        port=port,
        username=username,
        password=password,
        interval=interval,
    )
    app.run()


if __name__ == "__main__":
    main()
