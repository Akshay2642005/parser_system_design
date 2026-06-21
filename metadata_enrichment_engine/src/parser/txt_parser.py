"""Parse metadata TXT files into RawMetadata models."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from src.models.metadata import (
    ColumnInfo,
    ConstraintInfo,
    DatabaseInfo,
    DatabaseType,
    IndexInfo,
    RelationshipInfo,
    RelationshipType,
    RawMetadata,
    TableInfo,
)

logger = logging.getLogger(__name__)

# Section pattern: [SECTION_NAME]
_SECTION_RE = re.compile(r"^\[([A-Z_]+)]\s*$")
# Key=value pattern
_KV_RE = re.compile(r"^([a-zA-Z_]+)\s*=\s*(.*)$")


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


def _parse_int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_metadata_txt(path: str | Path, db_info: DatabaseInfo | None = None) -> RawMetadata:
    """Parse a metadata TXT file and return a RawMetadata object.

    The parser is streaming-friendly: it reads line-by-line without loading
    the entire file into memory, supporting large files with thousands of
    tables.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")

    metadata = RawMetadata(database=db_info or DatabaseInfo())
    current_section: str | None = None
    current_table: TableInfo | None = None
    current_column: ColumnInfo | None = None
    current_index: IndexInfo | None = None
    current_constraint: ConstraintInfo | None = None
    table_map: dict[str, TableInfo] = {}

    def _flush_column() -> None:
        nonlocal current_column
        if current_column is not None and current_table is not None:
            current_column.table_name = current_table.name
            current_table.columns.append(current_column)
            current_column = None

    def _flush_index() -> None:
        nonlocal current_index
        if current_index is not None and current_table is not None:
            current_index.table_name = current_table.name
            current_table.indexes.append(current_index)
            current_index = None

    def _flush_constraint() -> None:
        nonlocal current_constraint
        if current_constraint is not None and current_table is not None:
            current_constraint.table_name = current_table.name
            current_table.constraints.append(current_constraint)
            current_constraint = None

    def _flush_table() -> None:
        nonlocal current_table
        _flush_column()
        _flush_index()
        _flush_constraint()
        if current_table is not None:
            table_map[current_table.name] = current_table
            current_table = None

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n\r")
            if not line or line.startswith("#"):
                continue

            section_match = _SECTION_RE.match(line)
            if section_match:
                section_name = section_match.group(1)
                if section_name == "DATABASE" and current_section != "DATABASE":
                    # If we were in a table context, flush it
                    _flush_table()
                elif section_name == "TABLE":
                    _flush_table()
                    current_table = TableInfo()
                elif section_name == "COLUMN":
                    _flush_column()
                    _flush_index()
                    _flush_constraint()
                    current_column = ColumnInfo()
                elif section_name == "INDEX":
                    _flush_index()
                    current_index = IndexInfo()
                elif section_name == "CONSTRAINT":
                    _flush_constraint()
                    current_constraint = ConstraintInfo()
                elif section_name == "RELATIONSHIP":
                    _flush_column()
                    # Relationships are standalone
                current_section = section_name
                continue

            kv_match = _KV_RE.match(line)
            if not kv_match:
                continue

            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()

            if current_section == "DATABASE":
                if key == "name":
                    metadata.database.name = value
                elif key == "type":
                    try:
                        metadata.database.type = DatabaseType(value.lower())
                    except ValueError:
                        metadata.database.type = DatabaseType.UNKNOWN

            elif current_section == "TABLE" and current_table is not None:
                if key == "name":
                    current_table.name = value
                elif key == "row_count":
                    current_table.row_count = _parse_int_or_none(value)
                elif key == "comment":
                    current_table.comment = value

            elif current_section == "COLUMN" and current_column is not None:
                if key == "name":
                    current_column.name = value
                elif key == "type":
                    current_column.type = value
                elif key == "nullable":
                    current_column.nullable = _parse_bool(value)
                elif key == "primary_key":
                    current_column.primary_key = _parse_bool(value)
                elif key == "unique":
                    current_column.unique = _parse_bool(value)
                elif key == "default":
                    current_column.default = value
                elif key == "comment":
                    current_column.comment = value

            elif current_section == "INDEX" and current_index is not None:
                if key == "name":
                    current_index.name = value
                elif key == "columns":
                    current_index.columns = [c.strip() for c in value.split(",")]
                elif key == "unique":
                    current_index.unique = _parse_bool(value)

            elif current_section == "CONSTRAINT" and current_constraint is not None:
                if key == "name":
                    current_constraint.name = value
                elif key == "type":
                    current_constraint.type = value
                elif key == "columns":
                    current_constraint.columns = [c.strip() for c in value.split(",")]
                elif key == "referenced_table":
                    current_constraint.referenced_table = value
                elif key == "referenced_columns":
                    current_constraint.referenced_columns = [c.strip() for c in value.split(",")]

            elif current_section == "RELATIONSHIP":
                # Handle relationship lines as standalone key-value pairs
                if key == "from":
                    # Create a new relationship
                    if current_table is not None:
                        _flush_column()
                    rel = RelationshipInfo(from_column=value)
                    # We'll set to_column and type on subsequent lines
                    if current_table is not None:
                        current_table.relationships.append(rel)
                elif key == "to" and current_table and current_table.relationships:
                    current_table.relationships[-1].to_column = value
                elif key == "type" and current_table and current_table.relationships:
                    rel = current_table.relationships[-1]
                    try:
                        rel.type = RelationshipType(value.lower())
                    except ValueError:
                        rel.type = RelationshipType.INFERRED

    # Flush remaining
    _flush_table()

    # Move collected tables into metadata
    metadata.tables = list(table_map.values())

    # Extract primary keys from columns
    for table in metadata.tables:
        table.primary_keys = [
            col.name for col in table.columns if col.primary_key
        ]

    logger.info(
        "Parsed %d table(s) from %s", len(metadata.tables), path
    )
    return metadata
