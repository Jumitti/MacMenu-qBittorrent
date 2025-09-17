"""
MMqBt Plugin Template / Guide

This plugin serves as a reference to show how to structure and create a plugin
for MMqBt. It does not perform real actions on torrents but demonstrates:
- settings storage
- adding menu items
- run loop for the plugin
"""

import os
import json
import rumps

PLUGIN_NAME = "plugin_template"
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), f"{PLUGIN_NAME}_settings.json")

# Default settings for the plugin
DEFAULT_SETTINGS = {
    "example_option": True,
    "example_value": 10
}


def load_settings():
    """Load plugin settings from file or create default."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """Save plugin settings to file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def settings(app, plugin_menu):
    """
    Define settings menu items for the plugin.
    This function is called by MMqBt to populate the plugin submenu.
    """
    def edit_settings(_):
        settings_data = load_settings()
        response = rumps.Window(
            message=f"Current example value: {settings_data['example_value']}",
            title="Plugin Template Settings",
            default_text=str(settings_data['example_value']),
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 30),
        ).run()

        if response.clicked:
            try:
                settings_data['example_value'] = int(response.text)
                save_settings(settings_data)
                rumps.alert(f"Example value updated: {settings_data['example_value']}")
            except ValueError:
                rumps.alert("Invalid value. Enter an integer.")

    plugin_menu.add(rumps.MenuItem("Edit Settings", callback=edit_settings))

    def toggle_option(_):
        settings_data = load_settings()
        settings_data['example_option'] = not settings_data['example_option']
        save_settings(settings_data)
        state = "Enabled" if settings_data['example_option'] else "Disabled"
        rumps.alert(f"Example option is now {state}")

    plugin_menu.add(rumps.MenuItem("Toggle Option", callback=toggle_option))


def run(app):
    """
    Main plugin logic.
    This function is called periodically by MMqBt to perform plugin actions.
    """
    settings_data = load_settings()

    def show_settings(_):
        settings_text = json.dumps(settings_data, indent=2)
        # Alert popup
        rumps.alert(f"Current plugin settings:\n{settings_text}")
        # Notification macOS
        rumps.notification(
            "Plugin Settings",
            "Current settings loaded",
            settings_text
        )

    def show_credentials(_):
        # Alert popup
        rumps.alert(f"Current credentials:\nHost {app.host}:{app.port}\nUsername: {app.username}\nPassword: {app.password}")

    app.menu.add(rumps.MenuItem("DEMO TEMPLATE PLUGIN", callback=show_settings))
    app.menu.add(rumps.MenuItem("DEMO TEMPLATE CREDENTIALS", callback=show_credentials))
