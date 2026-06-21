"""Load YAML configuration files describing databases."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from src.models.metadata import DatabaseInfo, DatabaseType

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Single database entry from config."""
    id: str = ""
    type: DatabaseType = DatabaseType.UNKNOWN
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    """Top-level config schema."""
    databases: list[DatabaseConfig] = Field(default_factory=list)


def load_config(path: str | Path) -> AppConfig:
    """Read a YAML config file and return validated AppConfig."""
    path = Path(path)
    if not path.exists():
        logger.warning("Config file %s not found, returning empty config", path)
        return AppConfig()

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    config = AppConfig.model_validate(raw)
    logger.info("Loaded config with %d database(s)", len(config.databases))
    return config


def config_to_database_info(db_cfg: DatabaseConfig) -> DatabaseInfo:
    """Convert a DatabaseConfig entry to a DatabaseInfo model."""
    return DatabaseInfo(
        name=db_cfg.id,
        type=db_cfg.type,
    )
