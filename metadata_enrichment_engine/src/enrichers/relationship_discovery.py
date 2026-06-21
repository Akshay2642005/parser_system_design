"""Stage 3: Relationship Discovery — find implicit relationships."""

from __future__ import annotations

import logging

from src.models.metadata import (
    EnrichedDatabase,
    InferredRelationship,
    RawMetadata,
    RelationshipInfo,
)

logger = logging.getLogger(__name__)


def _col_parts(fqn: str) -> tuple[str, str]:
    """Split 'table.column' into (table, column)."""
    parts = fqn.split(".")
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", parts[0]


def _build_col_index(metadata: RawMetadata) -> dict[str, list[str]]:
    """Map column_name -> list of table names that have it."""
    idx: dict[str, list[str]] = {}
    for table in metadata.tables:
        for col in table.columns:
            idx.setdefault(col.name.lower(), []).append(table.name)
    return idx


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 3: discover inferred relationships."""
    col_index = _build_col_index(metadata)
    seen: set[tuple[str, str]] = set()

    # 1. Explicit FK relationships already parsed
    for rel in metadata.tables[0].relationships if metadata.tables else []:
        key = (rel.from_column, rel.to_column)
        if key not in seen:
            enriched.inferred_relationships.append(
                InferredRelationship(
                    from_column=rel.from_column,
                    to_column=rel.to_column,
                    confidence=0.95,
                    reason="Declared foreign key relationship",
                )
            )
            seen.add(key)

    # 2. Shared column name inference
    for table in metadata.tables:
        for col in table.columns:
            col_lower = col.name.lower()
            # Skip PKs to avoid self-references
            if col.primary_key:
                continue
            tables_with_col = col_index.get(col_lower, [])
            for other_table in tables_with_col:
                if other_table == table.name:
                    continue
                # Heuristic: if column ends with _id or _pk, it's likely FK
                if col_lower.endswith("_id") or col_lower.endswith("_pk"):
                    fk = (f"{table.name}.{col.name}", f"{other_table}.{col.name}")
                    if fk not in seen:
                        enriched.inferred_relationships.append(
                            InferredRelationship(
                                from_column=f"{table.name}.{col.name}",
                                to_column=f"{other_table}.{col.name}",
                                confidence=0.80,
                                reason=f"Shared identifier column '{col.name}'",
                            )
                        )
                        seen.add(fk)

    logger.info(
        "Relationship discovery: %d inferred relationship(s)",
        len(enriched.inferred_relationships),
    )
