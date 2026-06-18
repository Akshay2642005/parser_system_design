# AGENTS.md — MMS Parser System Design

## What this repo is

Design documentation and implementation scaffolding for an Airline MMS (Maintenance Management System) metadata pipeline.  
The enricher transforms raw DB metadata into AI-consumable enriched JSON. No executable code exists yet.

## Repository structure

```
├── AGENTS.md                         # This file — repo-wide orientation
├── README.md
│
├── enricher/                         # Python 3.12 enricher scaffolding
│   ├── AGENTS.md                     # Enricher-specific implementation guide
│   ├── rules/
│   │   └── name_dictionary.yaml      # Name mapping rules (only rule file written)
│   └── fixtures/                     # Empty, awaiting test data
│
└── docs/
    ├── architecture/
    │   ├── connector_parser_architecture.md   # 4-layer pipeline overall
    │   └── enricher_diagrams.md               # Mermaid diagrams
    ├── design/
    │   ├── parser_enricher_design.md          # Full enricher system design (1109 lines)
    │   └── plan.md                            # Implementation plan + module structure
    ├── api/
    │   ├── api_design.md                      # Quarkus REST API spec (80+ endpoints)
    │   └── openapi.json                       # Full OpenAPI 3.0 spec (109K)
    ├── database/
    │   ├── enriched_metadata_schema.json      # 11 entity types + examples
    │   └── MMS_Complete_Package.md            # 38 table definitions + full API ref
    └── business/
        └── mro_features.json                  # MRO feature hierarchy (6 functions)
```

## Key design docs (read in this order)

| File | What it covers |
|------|----------------|
| `docs/architecture/connector_parser_architecture.md` | Overall pipeline: Connector → Extractor → Enricher (6 stages) → Consumption |
| `docs/design/parser_enricher_design.md` | Full enricher system design: 6-stage pipeline, rules, error handling, deployment |
| `docs/database/enriched_metadata_schema.json` | Enriched JSON schema (11 entity types) + example instances |
| `docs/architecture/enricher_diagrams.md` | Mermaid diagrams for C4 context, pipeline detail, data flow, rule engine |
| `docs/api/api_design.md` | Quarkus REST API spec (JWT, RBAC: `mms:read/write/admin/certify`) |
| `docs/database/MMS_Complete_Package.md` | 38 PostgreSQL table definitions + full API + Quarkus code reference |
| `docs/design/plan.md` | Implementation plan: module structure, class design, execution modes, diagram |
| `docs/business/mro_features.json` | MRO business feature hierarchy (6 functions, ~20 features) |
| `docs/api/openapi.json` | Full OpenAPI 3.0 spec |

## Architecture highlights

- **4-layer pipeline**: Connector (Postgres/Cosmos/Oracle/MySQL/MSSQL) → Raw Extractor (schema discovery) → Enricher (6 deterministic stages) → Consumption (AI agent, RAG, vector store)
- **Enricher is rule-based, not LLM-based**. YAML rule files drive every stage. Same input → same output every time.
- **6 enrichment stages**: Name Enrichment → Feature & Reason Mapping → Relationship Discovery → Process & Endpoint Mapping → Glossary & Compliance → Use Case & Decision Generation
- **Single output artifact**: `enriched_metadata.json` — one file, 11 entity types
- **38 PostgreSQL tables** (transactional MMS), **3 CosmosDB containers** (events/audit/docs)
- **API is Quarkus/Java** (separate service from the enricher)
- **Enricher is Python 3.12** (Pydantic v2, YAML, structlog)
- **4 execution modes**: Full (<5min), Incremental (<30s), Rule-only (<30s), Validation/dry-run (<2min)
- **Warnings never halt pipeline**

## What this repo is NOT

- Not a monorepo or multi-package project
- Not a working application — no `main()`, no entrypoints, no deployable artifacts
- No framework quirks, no generated code, no migrations
- No testing infra, no fixtures, no snapshots
- No developer commands to run

If a contributor asks "how to run this" — the answer is "it's not built yet."
