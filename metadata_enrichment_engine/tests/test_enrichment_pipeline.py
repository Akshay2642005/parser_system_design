"""Tests for enrichment pipeline."""

from pathlib import Path

import pytest

from src.models.metadata import RawMetadata, DatabaseInfo, DatabaseType, TableInfo, ColumnInfo
from src.pipeline.enrichment_pipeline import enrich_single_database


@pytest.fixture
def sample_metadata() -> RawMetadata:
    return RawMetadata(
        database=DatabaseInfo(name="clinic_db", type=DatabaseType.POSTGRESQL),
        tables=[
            TableInfo(
                name="patients",
                columns=[
                    ColumnInfo(name="patient_id", type="INTEGER", nullable=False, primary_key=True),
                    ColumnInfo(name="email", type="VARCHAR(255)", nullable=True),
                    ColumnInfo(name="phone", type="VARCHAR(15)", nullable=True),
                    ColumnInfo(name="dob", type="DATE", nullable=True),
                ],
                primary_keys=["patient_id"],
            ),
            TableInfo(
                name="appointments",
                columns=[
                    ColumnInfo(name="appointment_id", type="INTEGER", nullable=False, primary_key=True),
                    ColumnInfo(name="patient_id", type="INTEGER", nullable=False),
                    ColumnInfo(name="status", type="VARCHAR(20)", nullable=False),
                ],
                primary_keys=["appointment_id"],
            ),
        ],
    )


def test_enrich_populates_domains(sample_metadata: RawMetadata) -> None:
    enriched = enrich_single_database(sample_metadata)
    assert len(enriched.domains) > 0
    assert enriched.domains[0].domain == "Healthcare"


def test_enrich_populates_glossary(sample_metadata: RawMetadata) -> None:
    enriched = enrich_single_database(sample_metadata)
    assert len(enriched.business_glossary) > 0
    terms = {g.term for g in enriched.business_glossary}
    assert "Patients" in terms


def test_enrich_populates_classifications(sample_metadata: RawMetadata) -> None:
    enriched = enrich_single_database(sample_metadata)
    pii_cols = {c.column for c in enriched.classifications}
    assert "email" in pii_cols
    assert "phone" in pii_cols
    assert "dob" in pii_cols


def test_enrich_populates_alerts(sample_metadata: RawMetadata) -> None:
    enriched = enrich_single_database(sample_metadata)
    assert len(enriched.alerts) > 0
    severities = {a.severity for a in enriched.alerts}
    assert "HIGH" in severities


def test_enrich_populates_use_cases(sample_metadata: RawMetadata) -> None:
    enriched = enrich_single_database(sample_metadata)
    assert len(enriched.use_cases) > 0


def test_enrich_populates_processes(sample_metadata: RawMetadata) -> None:
    enriched = enrich_single_database(sample_metadata)
    assert len(enriched.business_processes) > 0


def test_enrich_populates_names(sample_metadata: RawMetadata) -> None:
    enriched = enrich_single_database(sample_metadata)
    assert len(enriched.business_names) > 0
    name_map = {bn.technical_name: bn.business_name for bn in enriched.business_names}
    assert "dob" in name_map
    assert name_map["dob"] == "Date of birth"
