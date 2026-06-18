# MMS Parser System Design

Design documentation and implementation scaffolding for an Airline MMS (Maintenance Management System) metadata pipeline.

## Purpose

Transform raw database metadata (table schemas, columns, foreign keys) from a transactional MMS into **enriched JSON** that AI agents can consume. The enricher bridges the gap between technical database structures and airline MRO business language.

## Pipeline Overview

```
Raw DB Schema  →  Raw Metadata Extractor  →  Enricher (6 stages)  →  enriched_metadata.json  →  AI Agent
```

- **Connector layer** — Postgres (38 tables), Cosmos DB (3 containers), Oracle/MySQL/MSSQL
- **Extractor** — Schema discovery: columns, PKs, FKs, indexes, enums, stats
- **Enricher** — 6 deterministic stages driven by YAML rule files
- **Output** — Single `enriched_metadata.json` with 11 entity types

## Repository Structure

```
├── AGENTS.md                   # Repo-wide agent orientation
├── README.md
│
├── enricher/                   # Python 3.12 enricher scaffolding
│   ├── AGENTS.md               # Implementation-specific guidance
│   ├── rules/                  # YAML rule files (1 of 9 written)
│   └── fixtures/               # Test data (empty)
│
└── docs/
    ├── architecture/           # Pipeline architecture
    ├── design/                 # System design + implementation plan
    ├── api/                    # Quarkus REST API spec + OpenAPI
    ├── database/               # Schema definitions
    └── business/               # MRO feature definitions
```

## Key Documents

| File | What it covers |
|------|----------------|
| `docs/architecture/connector_parser_architecture.md` | Overall 4-layer pipeline architecture |
| `docs/design/parser_enricher_design.md` | Full enricher system design (1109 lines) |
| `docs/database/enriched_metadata_schema.json` | Enriched JSON schema + example instances |
| `docs/architecture/enricher_diagrams.md` | Mermaid diagrams for every subsystem |
| `docs/api/api_design.md` | Quarkus REST API spec (80+ endpoints) |
| `docs/design/plan.md` | Implementation plan with module structure + diagram |
| `docs/business/mro_features.json` | MRO business feature hierarchy |
| `docs/api/openapi.json` | Full OpenAPI 3.0 spec |

## Implementation Status

- **Design**: Complete (architecture + schema + diagrams)
- **Rules**: `enricher/rules/name_dictionary.yaml` exists (10 tables mapped); ~8 more YAML rule files to write
- **Code**: Not yet built — this repo is design-only

## Tech Stack (planned)

| Component | Choice |
|-----------|--------|
| Enricher | Python 3.12+ / Pydantic v2 |
| API | Quarkus / Java (separate service) |
| Database | PostgreSQL (38 tables) + Cosmos DB (3 containers) |
| Rules | YAML (domain SME editable, no code changes) |
| Container | Docker |
| CI/CD | GitHub Actions |
