import json
import os

PREFS_FILE = "user_prefs.json"

DEFAULT_PREFS = { # default preferences
    "graph_bg": "dark",
    "graph_line_color": "yellow"
}

def load_prefs() -> dict:
    if not os.path.exists(PREFS_FILE):
        return DEFAULT_PREFS.copy()
    try:
        with open(PREFS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # ensure defaults exist if file is partial
            return {**DEFAULT_PREFS, **data}
    except (json.JSONDecodeError, IOError):
        return DEFAULT_PREFS.copy()

def save_prefs(prefs: dict) -> None:
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=4)
    except IOError:
        pass
