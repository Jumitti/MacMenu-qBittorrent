# MMqBt Plugin Development Guide

This guide explains how to create custom plugins for **MMqBt**, the macOS menu bar app for qBittorrent.  
It covers the **structure, required functions, settings handling, and menu integration**.

---

## Plugin Structure

A plugin is a Python file placed in the `plugins/` folder of MMqBt.  
At minimum, a plugin should define:

1. **Settings storage**
2. **Settings menu items**
3. **Run logic**

You also have a template here: [template.py](template.py)

### Example skeleton

```python
import os
import json
import rumps

PLUGIN_NAME = "my_plugin"
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), f"{PLUGIN_NAME}_settings.json")

DEFAULT_SETTINGS = {
    "example_option": True,
    "example_value": 10
}
````

---

## 1. Settings

Plugins store configuration in a **JSON file**, named `<plugin_name>_settings.json`.

### Load settings

```python
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return DEFAULT_SETTINGS.copy()
```

### Save settings

```python
def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
```

---

## 2. Plugin Settings Menu

Use the `settings(app, plugin_menu)` function to add configurable menu items.

```python
def settings(app, plugin_menu):
    def toggle_option(_):
        data = load_settings()
        data['example_option'] = not data['example_option']
        save_settings(data)
        state = "Enabled" if data['example_option'] else "Disabled"
        rumps.alert(f"Example option is now {state}")

    plugin_menu.add(rumps.MenuItem("Toggle Option", callback=toggle_option))

    def edit_value(_):
        data = load_settings()
        response = rumps.Window(
            message=f"Current value: {data['example_value']}",
            title="Edit Value",
            default_text=str(data['example_value']),
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 30)
        ).run()

        if response.clicked:
            try:
                data['example_value'] = int(response.text)
                save_settings(data)
                rumps.alert(f"Value updated to {data['example_value']}")
            except ValueError:
                rumps.alert("Invalid value. Enter an integer.")

    plugin_menu.add(rumps.MenuItem("Edit Value", callback=edit_value))
```

* `plugin_menu` is a **submenu object** under the plugin.
* Each menu item must have a callback function.

---

## 3. Main Plugin Logic

The `run(app)` function is called periodically by MMqBt.

```python
def run(app):
    settings_data = load_settings()
    print(f"[My Plugin] Running with settings: {settings_data}")
    
    def show_settings(_):
        settings_text = json.dumps(settings_data, indent=2)
        rumps.alert(f"Current plugin settings:\n{settings_text}")
        rumps.notification("Plugin Settings", "Current settings loaded", settings_text)
    
    plugin_menu = rumps.MenuItem("Show Settings", callback=show_settings)
    app.menu.add(plugin_menu)
```

---

## 4. Best Practices

* All ``self`` references in ``core.py`` can be used. For example, ``self.host`` would become ``app.host`` in the plugin.
* Always use `load_settings()` and `save_settings()` to read/write plugin configuration.
* Use descriptive names for your menu items.
* Keep your plugin self-contained; do not modify MMqBt internal state directly unless necessary.
* For asynchronous tasks, consider using `threading.Thread` or `asyncio` to avoid blocking the menu.
* Document your plugin settings clearly in comments or in the plugin itself.
* **Debugging tip:** 
  - To debug your plugin more easily, fork the MMqBt project and run it in a console. This allows you to see print statements, exceptions, and log output in real-time.
  - Currently, there is no reliable way to integrate non-compiled Python packages directly into the compiled `.app`. Therefore, plugin development should be done via a fork: you can test your plugin in the development environment, and once it's ready, the `.app` can be rebuilt with the correct dependencies included.

---

## 5. Optional Features

* Send notifications using `rumps.notification(title, subtitle, message)`.
* Create submenus for advanced configuration.
* Integrate with external APIs (Telegram, Discord, etc.).

---

## Example Plugin Workflow

1. Load settings.
2. Add menu items to `plugin_menu` using `settings(app, plugin_menu)`.
3. Periodically run plugin logic in `run(app)`.
4. Optionally, display alerts or notifications.
5. Save any updated settings to JSON.

---

## Contributing

We welcome contributions to the plugin system! Here’s how you can help:

1. **Fork the repository**  
   This allows you to develop and test plugins in a local environment.

2. **Develop your plugin**  
   - Ensure your plugin is self-contained and does not modify MMqBt’s internal state unnecessarily.  
   - Test your plugin thoroughly in your fork before submitting.

3. **Follow best practices**  
   - Use `load_settings()` and `save_settings()` for configuration.  
   - Use descriptive menu item names.  
   - For asynchronous tasks, consider `threading.Thread` or `asyncio` to avoid blocking the menu.  
   - Document your plugin settings clearly.

4. **Submit a pull request**  
   - Include a clear description of what your plugin does.  
   - Provide instructions for setup and usage if necessary.  
   - Keep in mind that we may request changes or improvements before merging.

**Important:** Currently, adding external dependencies to plugins in the compiled `.app` is not supported. To develop a plugin with dependencies, you will need to fork the project and run MMqBt in a development environment where you can install the necessary packages. Once the plugin is ready, it can be integrated into the main project and included in the compiled `.app`.


