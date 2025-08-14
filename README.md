# MacMenu-qBittorrent 🍏

![PyPI version](https://img.shields.io/pypi/v/macmenuqbt?label=PyPI%20Version)


MacMenu-qBittorrent is a lightweight macOS menu bar app that connects to qBittorrent's Web UI and displays active torrents with their progress and other stuff directly in your Mac menu bar.

---

## Features

- Runs natively on macOS as a menu bar application.
- Connects to qBittorrent Web UI via `qbittorrent-api`.
- Displays all active torrents with progress percentages **and many other stuff** in the menu bar.
- Configuration displaying
- Auto-refreshes torrent status at configurable intervals.
- Configurable connection parameters (host, port, username, password).
- Simple and clean UI using `rumps`.

---

## Installation via PyPI

1. **Ensure you have Python >=3.8 installed on your Mac**

2. **Install the package from PyPI**

    ```bash
    pip install macmenuqbt
    ```

---

## Usage from the command line

Run the app from your terminal (or create a shortcut) — this will start the menu bar app:

```bash
macmenuqbt
# or the alias
mmqbt
```

Available options:
```bash
macmenuqbt --host localhost --port 8080 --username admin --password 123456 --interval 5
```
| Argument     | Alias(s) | Description                     | Default Value |
|--------------|----------|---------------------------------|---------------|
| `--host`     | `-H`     | qBittorrent Web UI host         | `localhost`   |
| `--port`     | `-P`     | qBittorrent Web UI port         | `8080`        |
| `--username` | `-U`     | qBittorrent Web UI username     | `admin`       |
| `--password` | `-PSW`   | qBittorrent Web UI password     | `123456`      |
| `--interval` | `-I`     | Update interval in seconds      | `5`           |
| `--version`  | `-V`     | Show program version and exit   |               |
| `--help`     |          | Show this help message and exit |               |


For help and version:
```bash
macmenuqbt --help
macmenuqbt --version
```

## Usage as a Python module
You can also embed Menubar-qBittorrent in your own Python scripts by calling its main() function with parameters:

```python
from macmenuqbt.core import main as mmqbt

mmqbt(
    host="localhost",
    port=8080,
    username="admin",
    password="123456",
    interval=5
)
```

## Screenshot and hints

- This is the default view:
   ![alt text](img/set_options.png)

- Status table (see also screenshot):

   | Status              | Emoji | Description                    |
   |---------------------|-------|--------------------------------|
   | downloading         | ⬇️    | Downloading                    |
   | resumed             | ⬇️    | Download resumed               |
   | running             | ⬇️    | Running / in progress          |
   | forcedDL            | ⬇️    | Forced download                |
   | seeding             | 🌱    | Seeding (uploading)            |
   | completed           | ✅     | Download completed             |
   | paused              | ⏸️    | Paused                         |
   | stopped             | ⏸️    | Stopped                        |
   | inactive            | ⏸️    | Inactive                       |
   | active              | 🔄    | Active / operation in progress |
   | stalled             | ⚠️    | Stalled / waiting              |
   | stalled_uploading   | ⚠️    | Upload stalled                 |
   | stalled_downloading | ⚠️    | Download stalled               |
   | checking            | 🔍    | Checking files                 |
   | moving              | 📦    | Moving files                   |
   | errored             | ❌     | Error encountered              |
   | all                 | 📋    | All torrents                   |
   | unknown             | ❓     | Unknown status                 |

   ![alt text](img/status.png)

- All options enabled:

  Simply click on them to activate them.
  ![alt text](img/full_options.png)

- Change the order as you wish:

   ![alt text](img/manage_down.png)
   ![alt text](img/manage_down_2.png)


## Notes
Only compatible with macOS due to use of rumps for menu bar integration.

Tested with Python 3.8+ and qBittorrent Web UI 5.x.

Requires qBittorrent Web UI to be enabled and accessible.

## Disclaimer
This tool only displays torrent information; it does not modify or control qBittorrent.

## Contributing
Feel free to open issues or submit pull requests!

## Another qBittorrent plugin

- [TrackersRemover-qBittorent](https://github.com/Jumitti/TrackersRemover-qBittorrent): as expected
