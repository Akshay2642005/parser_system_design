"""Tests for config loader."""

from pathlib import Path

import pytest

from src.parser.config_loader import AppConfig, load_config


VALID_CONFIG = """\
databases:
  - id: clinic_db
    type: postgresql
    description: "Clinic database"

  - id: hr_db
    type: mysql
"""


@pytest.fixture
def valid_config(tmp_path: Path) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(VALID_CONFIG, encoding="utf-8")
    return p


def test_load_valid_config(valid_config: Path) -> None:
    config = load_config(valid_config)
    assert len(config.databases) == 2
    assert config.databases[0].id == "clinic_db"
    assert config.databases[1].type.value == "mysql"


def test_load_missing_config() -> None:
    config = load_config(Path("/nonexistent/config.yaml"))
    assert config.databases == []


def test_empty_config(tmp_path: Path) -> None:
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    config = load_config(p)
    assert config.databases == []
