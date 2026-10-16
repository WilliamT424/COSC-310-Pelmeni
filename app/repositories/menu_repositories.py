import json
import os
import tempfile
from pathlib import Path

current_dir = Path(__file__).resolve().parent.parent.parent
MENUS_FILE = current_dir / "data" / "menus.json"


def read_menus_file(file_path=None):
    # Resolved at call time so tests can point MENUS_FILE at a temp copy
    with open(file_path or MENUS_FILE, "r") as file:
        data = json.load(file)

    return data


def write_menus_file(data, file_path=None):
    file_path = file_path or MENUS_FILE
    # Write to a temp file then replace, so a crash mid-write can't corrupt menus.json
    fd, tmp_path = tempfile.mkstemp(dir=Path(file_path).parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as tmp:
            json.dump(data, tmp, indent=2)
        os.replace(tmp_path, file_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

