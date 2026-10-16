import json
import os
import tempfile
from pathlib import Path

current_dir = Path(__file__).resolve().parent.parent.parent


def read_menus_file(file_path=current_dir / "data" / "menus.json"):

    with open(file_path, "r") as file:
        data = json.load(file)

    return data


def write_menus_file(data, file_path=current_dir / "data" / "menus.json"):
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

