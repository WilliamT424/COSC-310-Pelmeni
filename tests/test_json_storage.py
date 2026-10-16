import json

import pytest

from app.repositories.json_storage import atomic_write_json


def test_atomic_write_json_writes_data(tmp_path):
    path = tmp_path / "data.json"
    atomic_write_json([{"id": 1}], path)
    assert json.loads(path.read_text()) == [{"id": 1}]


def test_atomic_write_json_failure_keeps_original_file_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('[{"id": 1}]')

    with pytest.raises(TypeError):
        atomic_write_json([{"id": object()}], path)  # not JSON serializable

    assert json.loads(path.read_text()) == [{"id": 1}]
    assert list(tmp_path.glob("*.tmp")) == []
