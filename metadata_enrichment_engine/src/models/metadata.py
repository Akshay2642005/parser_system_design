"""Pydantic models for raw and enriched metadata."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    SQLITE = "sqlite"
    UNKNOWN = "unknown"


class RelationshipType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    INFERRED = "inferred"


class ComplianceClassification(str, Enum):
    PII = "PII"
    PHI = "PHI"
    PCI = "PCI"
    SENSITIVE = "Sensitive"
    FINANCIAL = "Financial"
    NONE = "None"


class AlertSeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ---------------------------------------------------------------------------
# Raw metadata models
# ---------------------------------------------------------------------------

class DatabaseInfo(BaseModel):
    """Technical database info as parsed from TXT."""
    name: str = ""
    type: DatabaseType = DatabaseType.UNKNOWN


class ColumnInfo(BaseModel):
    """Raw column metadata."""
    name: str = ""
    table_name: str = ""
    type: str = ""
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default: str | None = None
    comment: str | None = None


class IndexInfo(BaseModel):
    name: str = ""
    table_name: str = ""
    columns: list[str] = Field(default_factory=list)
    unique: bool = False


class ConstraintInfo(BaseModel):
    name: str = ""
    table_name: str = ""
    type: str = ""
    columns: list[str] = Field(default_factory=list)
    referenced_table: str | None = None
    referenced_columns: list[str] = Field(default_factory=list)


class RelationshipInfo(BaseModel):
    from_column: str = ""
    to_column: str = ""
    type: RelationshipType = RelationshipType.INFERRED


class TableInfo(BaseModel):
    """Raw table metadata."""
    name: str = ""
    columns: list[ColumnInfo] = Field(default_factory=list)
    primary_keys: list[str] = Field(default_factory=list)
    indexes: list[IndexInfo] = Field(default_factory=list)
    constraints: list[ConstraintInfo] = Field(default_factory=list)
    relationships: list[RelationshipInfo] = Field(default_factory=list)
    row_count: int | None = None
    comment: str | None = None


class RawMetadata(BaseModel):
    """Complete raw metadata parsed from TXT + config."""
    database: DatabaseInfo = Field(default_factory=DatabaseInfo)
    tables: list[TableInfo] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Enrichment output models
# ---------------------------------------------------------------------------

class BusinessName(BaseModel):
    technical_name: str = ""
    business_name: str = ""
    human_readable_description: str = ""


class DomainScore(BaseModel):
    domain: str = ""
    confidence: float = 0.0


class InferredRelationship(BaseModel):
    from_column: str = ""
    to_column: str = ""
    confidence: float = 0.0
    reason: str = ""


class GlossaryEntry(BaseModel):
    term: str = ""
    definition: str = ""


class ClassificationEntry(BaseModel):
    column: str = ""
    table: str = ""
    classification: ComplianceClassification = ComplianceClassification.NONE
    reason: str = ""


class UseCase(BaseModel):
    name: str = ""
    description: str = ""


class BusinessProcess(BaseModel):
    process: str = ""
    description: str = ""
    tables_involved: list[str] = Field(default_factory=list)


class Alert(BaseModel):
    severity: AlertSeverity = AlertSeverity.INFO
    message: str = ""
    table: str | None = None
    column: str | None = None


class EnrichedDatabase(BaseModel):
    """Single enriched database document."""
    database_info: DatabaseInfo = Field(default_factory=DatabaseInfo)
    tables: list[TableInfo] = Field(default_factory=list)
    relationships: list[RelationshipInfo] = Field(default_factory=list)
    inferred_relationships: list[InferredRelationship] = Field(default_factory=list)
    domains: list[DomainScore] = Field(default_factory=list)
    business_glossary: list[GlossaryEntry] = Field(default_factory=list)
    classifications: list[ClassificationEntry] = Field(default_factory=list)
    use_cases: list[UseCase] = Field(default_factory=list)
    business_processes: list[BusinessProcess] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    business_names: list[BusinessName] = Field(default_factory=list)


class EnrichedOutput(BaseModel):
    """Top-level output wrapping one or more enriched databases."""
    databases: list[EnrichedDatabase] = Field(default_factory=list)
