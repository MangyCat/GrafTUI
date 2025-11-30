import json
import os

WORKSPACE_FILE = "graftui_workspace.json"

def load_workspace():
    if not os.path.exists(WORKSPACE_FILE):
        return None
    try:
        with open(WORKSPACE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def save_workspace(state):
    try:
        with open(WORKSPACE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except IOError as e:
        print(f"Error saving workspace: {e}")
