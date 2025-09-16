import rumps
import json
import os

SETTINGS_FILENAME = __file__.replace(".py", "_settings.json")

DEFAULT_SETTINGS = {
    "min_dl": 10
}

IGNORED_TRACKERS = {"** [DHT] **", "** [PeX] **", "** [LSD] **"}


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


def settings(app, plugin_menu):
    def credentials(_):
        plugin_settings = load_settings()

        response = rumps.Window(
            message="Current value (Kb/s) : {}".format(plugin_settings["min_dl"]),
            title="Change the minimum DL speed before deleting trackers (Kb/s)",
            default_text=str(plugin_settings["min_dl"]),
            ok="Done",
            cancel="Cancel",
            dimensions=(400, 30),
        ).run()

        if response.clicked:
            try:
                new_value = int(response.text)
                plugin_settings["min_dl"] = new_value
                save_settings(plugin_settings)
                rumps.alert(f"Min DL updated: {new_value} Kb/s")
            except ValueError:
                rumps.alert("Invalid value. Enter an integer.")

    plugin_menu.add(rumps.MenuItem("Credentials", callback=credentials))


def run(app):
    plugin_settings = load_settings()
    MIN_DL_SPEED = plugin_settings["min_dl"]
    previous_snapshot = {}
    current_snapshot = {}

    torrents_to_clean = [t for t in app.list_torrent if
                         t.state in ['downloading', 'forcedDL'] and t.dlspeed > MIN_DL_SPEED * 1024]

    for torrent in torrents_to_clean:
        current_trackers = app.client.torrents_trackers(torrent.hash)

        for tr in current_trackers:
            if tr.url in IGNORED_TRACKERS:
                continue

            app.client.torrents_remove_trackers(
                torrent_hash=torrent.hash,
                urls=[tr.url]
            )
            rumps.notification("🎉 Tracker deleted !", subtitle=torrent.name, message=f"{tr.url}",
                               sound=app.settings_data['Notification sound'])

