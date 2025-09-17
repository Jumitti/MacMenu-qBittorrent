import rumps
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QFileDialog, QMessageBox
)
import json
import os

SETTINGS_FILENAME = __file__.replace(".py", "_settings.json")

DEFAULT_SETTINGS = {
    "min_dl": 10,
    "ignored_trackers": ["** [DHT] **", "** [PeX] **", "** [LSD] **"]
}


def load_settings():
    if os.path.exists(SETTINGS_FILENAME):
        with open(SETTINGS_FILENAME, "r") as f:
            return json.load(f)
    else:
        with open(SETTINGS_FILENAME, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILENAME, "w") as f:
        json.dump(settings, f, indent=2)


class TrackerSettings(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plugin Settings")
        self.resize(500, 400)

        self.settings = load_settings()

        main_layout = QVBoxLayout()

        # Min DL
        dl_layout = QHBoxLayout()
        dl_layout.addWidget(QLabel("Min DL (KB/s):"))
        self.min_dl_edit = QLineEdit(str(self.settings.get("min_dl", 10)))
        dl_layout.addWidget(self.min_dl_edit)
        main_layout.addLayout(dl_layout)

        # Add tracker
        tracker_layout = QHBoxLayout()
        tracker_layout.addWidget(QLabel("Add tracker:"))
        self.tracker_edit = QLineEdit()
        tracker_layout.addWidget(self.tracker_edit)
        self.btn_add = QPushButton("Add")
        self.btn_add.clicked.connect(self.add_tracker)
        tracker_layout.addWidget(self.btn_add)
        self.btn_add_file = QPushButton("Add from file")
        self.btn_add_file.clicked.connect(self.add_from_file)
        tracker_layout.addWidget(self.btn_add_file)
        main_layout.addLayout(tracker_layout)

        # Ignored trackers list
        self.tracker_list = QListWidget()
        self.tracker_list.addItems(self.settings.get("ignored_trackers", []))
        main_layout.addWidget(QLabel("Ignored trackers:"))
        main_layout.addWidget(self.tracker_list)

        # Remove / Reset buttons
        btn_layout = QHBoxLayout()
        self.btn_remove = QPushButton("Remove selected")
        self.btn_remove.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.btn_remove)
        self.btn_reset = QPushButton("Reset default")
        self.btn_reset.clicked.connect(self.reset_default)
        btn_layout.addWidget(self.btn_reset)
        main_layout.addLayout(btn_layout)

        # Save button
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.clicked.connect(self.save)
        main_layout.addWidget(self.btn_save)

        self.setLayout(main_layout)

    def add_tracker(self):
        tracker = self.tracker_edit.text().strip()
        if not tracker:
            QMessageBox.warning(self, "Warning", "Tracker cannot be empty")
            return
        items = [self.tracker_list.item(i).text() for i in range(self.tracker_list.count())]
        if tracker in items:
            QMessageBox.information(self, "Info", "Tracker already in the list")
            return
        self.tracker_list.addItem(tracker)
        self.tracker_edit.clear()

    def add_from_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select tracker file", "", "Text files (*.txt);;All files (*)")
        if not filepath:
            return
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                tracker = line.strip()
                if tracker and tracker not in [self.tracker_list.item(i).text() for i in range(self.tracker_list.count())]:
                    self.tracker_list.addItem(tracker)

    def remove_selected(self):
        for item in self.tracker_list.selectedItems():
            self.tracker_list.takeItem(self.tracker_list.row(item))

    def reset_default(self):
        self.tracker_list.clear()
        self.tracker_list.addItems(DEFAULT_SETTINGS["ignored_trackers"])

    def save(self):
        try:
            min_dl = int(self.min_dl_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Warning", "Min DL must be an integer")
            return
        trackers = [self.tracker_list.item(i).text() for i in range(self.tracker_list.count())]
        self.settings["min_dl"] = min_dl
        self.settings["ignored_trackers"] = trackers
        save_settings(self.settings)
        QMessageBox.information(self, "Saved", "Settings saved successfully.")


def settings(app, plugin_menu):
    def settings_trqbt(_):
        app = QApplication(sys.argv)
        w = TrackerSettings()
        w.show()
        sys.exit(app.exec_())

    plugin_menu.add(rumps.MenuItem("Settings", callback=settings_trqbt))


def run(app):
    plugin_settings = load_settings()
    MIN_DL_SPEED = plugin_settings["min_dl"]
    ignored_trackers = set(plugin_settings.get("ignored_trackers", []))

    torrents_to_clean = [
        t for t in app.list_torrent
        if t.state in ['downloading', 'forcedDL'] and t.dlspeed > MIN_DL_SPEED * 1024
    ]

    for torrent in torrents_to_clean:
        current_trackers = app.client.torrents_trackers(torrent.hash)

        for tr in current_trackers:
            if tr.url in ignored_trackers:
                continue

            try:
                app.client.torrents_remove_trackers(
                    torrent_hash=torrent.hash,
                    urls=[tr.url]
                )
                rumps.notification(
                    "🎉 Tracker deleted !",
                    subtitle=torrent.name,
                    message=f"{tr.url}",
                    sound=app.settings_data.get('Notification sound', False)
                )
            except Exception as e:
                rumps.notification(
                    "⚠️ Error removing tracker",
                    subtitle=torrent.name,
                    message=f"{tr.url} - {e}",
                    sound=False
                )