"""Tests for TXT parser."""

from pathlib import Path

import pytest

from src.models.metadata import DatabaseInfo, DatabaseType
from src.parser.txt_parser import parse_metadata_txt

SAMPLE_TXT = """\
[DATABASE]
name=clinic_db
type=postgresql

[TABLE]
name=patients

[COLUMN]
name=patient_id
type=INTEGER
nullable=false
primary_key=true

[COLUMN]
name=phone
type=VARCHAR(15)

[COLUMN]
name=dob
type=DATE

[TABLE]
name=appointments

[COLUMN]
name=appointment_id
type=INTEGER
primary_key=true

[COLUMN]
name=patient_id
type=INTEGER

[RELATIONSHIP]
from=appointments.patient_id
to=patients.patient_id
type=many_to_one
"""


@pytest.fixture
def sample_txt(tmp_path: Path) -> Path:
    p = tmp_path / "sample.txt"
    p.write_text(SAMPLE_TXT, encoding="utf-8")
    return p


def test_parse_database_info(sample_txt: Path) -> None:
    meta = parse_metadata_txt(sample_txt)
    assert meta.database.name == "clinic_db"
    assert meta.database.type == DatabaseType.POSTGRESQL


def test_parse_tables(sample_txt: Path) -> None:
    meta = parse_metadata_txt(sample_txt)
    assert len(meta.tables) == 2
    names = {t.name for t in meta.tables}
    assert names == {"patients", "appointments"}


def test_parse_columns(sample_txt: Path) -> None:
    meta = parse_metadata_txt(sample_txt)
    patients = next(t for t in meta.tables if t.name == "patients")
    assert len(patients.columns) == 3
    col_names = [c.name for c in patients.columns]
    assert col_names == ["patient_id", "phone", "dob"]


def test_parse_primary_keys(sample_txt: Path) -> None:
    meta = parse_metadata_txt(sample_txt)
    patients = next(t for t in meta.tables if t.name == "patients")
    assert "patient_id" in patients.primary_keys


def test_parse_relationships(sample_txt: Path) -> None:
    meta = parse_metadata_txt(sample_txt)
    appointments = next(t for t in meta.tables if t.name == "appointments")
    assert len(appointments.relationships) == 1
    rel = appointments.relationships[0]
    assert rel.from_column == "appointments.patient_id"
    assert rel.to_column == "patients.patient_id"


def test_parse_with_db_info(tmp_path: Path) -> None:
    p = tmp_path / "minimal.txt"
    p.write_text("[TABLE]\nname=foo\n\n[COLUMN]\nname=bar\ntype=INT\n", encoding="utf-8")
    info = DatabaseInfo(name="test_db", type=DatabaseType.MYSQL)
    meta = parse_metadata_txt(p, db_info=info)
    assert meta.database.name == "test_db"
    assert meta.database.type == DatabaseType.MYSQL


def test_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        parse_metadata_txt(Path("/nonexistent/file.txt"))
