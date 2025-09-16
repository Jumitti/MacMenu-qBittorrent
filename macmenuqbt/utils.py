import os, sys
from importlib import resources

def get_icon(name: str) -> str:
    if getattr(sys, "frozen", False):  # si packagé avec PyInstaller
        base_path = sys._MEIPASS
        return os.path.join(base_path, "macmenuqbt", "icon", name)
    else:
        return str(resources.files("macmenuqbt") / "icon" / name)
