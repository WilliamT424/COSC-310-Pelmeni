import json
import os
import tempfile
from pathlib import Path


def atomic_write_json(data, file_path, indent=2):
    # Write to a temp file then replace, so a crash mid-write can't corrupt the data file
    file_path = Path(file_path)
    fd, tmp_path = tempfile.mkstemp(dir=file_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as tmp:
            json.dump(data, tmp, indent=indent)
        os.replace(tmp_path, file_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
