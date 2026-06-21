"""Stage 8: Decision & Alert Generation — flag schema quality issues."""

from __future__ import annotations

import logging

from src.models.metadata import (
    Alert,
    AlertSeverity,
    ComplianceClassification,
    EnrichedDatabase,
    RawMetadata,
)

logger = logging.getLogger(__name__)


def _check_missing_primary_keys(
    metadata: RawMetadata, enriched: EnrichedDatabase
) -> None:
    for table in metadata.tables:
        if not table.primary_keys:
            enriched.alerts.append(
                Alert(
                    severity=AlertSeverity.HIGH,
                    message=f"Table '{table.name}' has no primary key defined",
                    table=table.name,
                )
            )


def _check_empty_tables(
    metadata: RawMetadata, enriched: EnrichedDatabase
) -> None:
    for table in metadata.tables:
        if not table.columns:
            enriched.alerts.append(
                Alert(
                    severity=AlertSeverity.MEDIUM,
                    message=f"Table '{table.name}' has no columns defined",
                    table=table.name,
                )
            )


def _check_pii_without_masking(
    metadata: RawMetadata, enriched: EnrichedDatabase
) -> None:
    pii_cols = {
        (c.table, c.column) for c in enriched.classifications
        if c.classification in (ComplianceClassification.PII, ComplianceClassification.PHI)
    }

    for table in metadata.tables:
        for col in table.columns:
            if (table.name, col.name) in pii_cols:
                has_masking_hint = any(
                    keyword in col.name.lower()
                    for keyword in ("masked", "hash", "token", "encrypted", "redacted")
                )
                if not has_masking_hint:
                    enriched.alerts.append(
                        Alert(
                            severity=AlertSeverity.HIGH,
                            message=(
                                f"Table '{table.name}' contains PII/PHI field "
                                f"'{col.name}' but no masking policy metadata exists"
                            ),
                            table=table.name,
                            column=col.name,
                        )
                    )


def _check_excessive_nullable(
    metadata: RawMetadata, enriched: EnrichedDatabase
) -> None:
    for table in metadata.tables:
        if not table.columns:
            continue
        nullable_count = sum(1 for c in table.columns if c.nullable)
        ratio = nullable_count / len(table.columns)
        if ratio > 0.8:
            enriched.alerts.append(
                Alert(
                    severity=AlertSeverity.MEDIUM,
                    message=(
                        f"Table '{table.name}' has {nullable_count}/{len(table.columns)} "
                        f"nullable columns ({ratio:.0%}). Consider tightening nullability."
                    ),
                    table=table.name,
                )
            )


def _check_weak_relationships(
    metadata: RawMetadata, enriched: EnrichedDatabase
) -> None:
    tables_with_no_rel = set()
    table_names = {t.name for t in metadata.tables}

    for table in metadata.tables:
        has_any_rel = False
        for col in table.columns:
            if col.name.lower().endswith("_id") and not col.primary_key:
                target = col.name.lower().replace("_id", "")
                for other in table_names:
                    if target in other.lower():
                        has_any_rel = True
                        break
            if has_any_rel:
                break
        if not has_any_rel and len(table.columns) > 1:
            tables_with_no_rel.add(table.name)

    if tables_with_no_rel:
        enriched.alerts.append(
            Alert(
                severity=AlertSeverity.LOW,
                message=(
                    f"Tables may lack relationship design: "
                    f"{', '.join(sorted(tables_with_no_rel)[:5])}"
                ),
            )
        )


def _check_composite_pk_heavy(
    metadata: RawMetadata, enriched: EnrichedDatabase
) -> None:
    for table in metadata.tables:
        if len(table.primary_keys) > 3:
            enriched.alerts.append(
                Alert(
                    severity=AlertSeverity.MEDIUM,
                    message=(
                        f"Table '{table.name}' has {len(table.primary_keys)} "
                        f"composite primary key columns. Consider surrogate keys."
                    ),
                    table=table.name,
                )
            )


def _generate_recommendations(enriched: EnrichedDatabase) -> None:
    """Generate actionable recommendations based on alerts."""
    recommendations: list[str] = []

    high_count = sum(1 for a in enriched.alerts if a.severity == AlertSeverity.HIGH)
    pii_count = sum(
        1 for c in enriched.classifications
        if c.classification in (ComplianceClassification.PII, ComplianceClassification.PHI)
    )

    if high_count > 0:
        recommendations.append(
            f"Address {high_count} HIGH severity alert(s) immediately."
        )

    if pii_count > 0:
        recommendations.append(
            f"Review {pii_count} PII/PHI classified columns for masking and access control."
        )

    if not enriched.domains:
        recommendations.append(
            "Domain could not be inferred. Consider adding table comments or "
            "increasing schema complexity for better classification."
        )

    if not enriched.use_cases:
        recommendations.append(
            "No use cases generated. Ensure table names are descriptive."
        )

    enriched.recommendations = recommendations


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 8: generate alerts and recommendations."""
    _check_missing_primary_keys(metadata, enriched)
    _check_empty_tables(metadata, enriched)
    _check_pii_without_masking(metadata, enriched)
    _check_excessive_nullable(metadata, enriched)
    _check_weak_relationships(metadata, enriched)
    _check_composite_pk_heavy(metadata, enriched)
    _generate_recommendations(enriched)

    logger.info(
        "Alert generation: %d alert(s), %d recommendation(s)",
        len(enriched.alerts),
        len(enriched.recommendations),
    )
