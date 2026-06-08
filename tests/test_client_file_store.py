"""Tests for client_file_store.FileStore."""
import json
import os
import tempfile

import pytest

from custom_components.myEnedis.client_file_store import FileStore


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def store(temp_dir):
    return FileStore(temp_dir, "test_pdl")


class TestReadAll:
    def test_empty_directory(self, store, temp_dir):
        assert store.read_all() == {}

    def test_none_path(self):
        store = FileStore(None, "test_pdl")
        assert store.read_all() == {}

    def test_single_json_file(self, store, temp_dir):
        with open(f"{temp_dir}/test.json", "w") as f:
            json.dump({"key": "value"}, f)
        result = store.read_all()
        assert result == {"test": {"key": "value"}}

    def test_multiple_json_files(self, store, temp_dir):
        with open(f"{temp_dir}/a.json", "w") as f:
            json.dump({"x": 1}, f)
        with open(f"{temp_dir}/b.json", "w") as f:
            json.dump({"y": 2}, f)
        result = store.read_all()
        assert result["a"] == {"x": 1}
        assert result["b"] == {"y": 2}

    def test_skips_non_json_files(self, store, temp_dir):
        with open(f"{temp_dir}/test.txt", "w") as f:
            f.write("not json")
        result = store.read_all()
        assert result == {}

    def test_corrupted_json_file(self, store, temp_dir):
        with open(f"{temp_dir}/bad.json", "w") as f:
            f.write("{invalid")
        result = store.read_all()
        assert result == {}


class TestWriteAll:
    def test_write_single_entry(self, store, temp_dir):
        store.write_all({"test": {"key": "value"}})
        filepath = f"{temp_dir}/test.json"
        assert os.path.exists(filepath)
        with open(filepath) as f:
            assert json.load(f) == {"key": "value"}

    def test_write_multiple_entries(self, store, temp_dir):
        store.write_all({"a": {"x": 1}, "b": {"y": 2}})
        with open(f"{temp_dir}/a.json") as f:
            assert json.load(f) == {"x": 1}
        with open(f"{temp_dir}/b.json") as f:
            assert json.load(f) == {"y": 2}

    def test_none_path(self):
        store = FileStore(None, "test_pdl")
        store.write_all({"test": {"key": "val"}})  # should not raise

    def test_skip_timeout_error(self, store, temp_dir):
        data = {
            "test": {
                "enedis_return": {"error": "UNKERROR_TIMEOUT"},
            }
        }
        store.write_all(data)
        assert not os.path.exists(f"{temp_dir}/test.json")
