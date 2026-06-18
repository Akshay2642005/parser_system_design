# Stage 2: Connector & Parser System Architecture
## Airline MMS Metadata Pipeline

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONNECTOR LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────┐  │
│  │ PostgresConn  │  │ CosmosConn   │  │OraConn   │  │ MySQLConn  │  │
│  │ (38 tables)   │  │ (3 containers)│  │(legacy)  │  │ (legacy)   │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  └─────┬──────┘  │
│         └──────────────┬──┴───────────────┴──────────────┘         │
│                        │                                           │
│               [Common Connector Interface]                          │
│                connect() | discover() | extract()                   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTRACTOR LAYER                                   │
│                                                                      │
│   Raw Metadata Extractor                                             │
│   ─────────────────────                                              │
│   Extracts per table:                                                │
│   ├── columns (name, type, length, nullable)                        │
│   ├── primary keys                                                   │
│   ├── foreign keys (with referenced table/column)                   │
│   ├── indexes (unique, composite)                                   │
│   ├── constraints (check, enum values, default)                     │
│   ├── comments (table + column level)                               │
│   ├── statistics (row count, size, null ratio)                      │
│   └── partitions (if any)                                           │
│                                                                      │
│   Output: raw_metadata.json                                          │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ENRICHER LAYER                                  │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ Stage 1:    │  │ Stage 2:     │  │ Stage 3:   │  │ Stage 4:   │ │
│  │ Name        │  │ Domain       │  │ Relationship│  │ Glossary & │ │
│  │ Enrichment  │  │ Mapping      │  │ Discovery  │  │ Compliance │ │
│  │ (NLP)       │  │ (rule engine)│  │ (FK graph) │  │ (keyword)  │ │
│  └─────────────┘  └──────────────┘  └────────────┘  └────────────┘ │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐                                  │
│  │ Stage 5:    │  │ Stage 6:     │                                  │
│  │ Use Case &  │  │ Decision &   │                                  │
│  │ Process Gen │  │ Alert Gen    │                                  │
│  │ (templates) │  │ (templates)  │                                  │
│  └─────────────┘  └──────────────┘                                  │
│                                                                      │
│   Output: enriched_metadata.json                                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 CONSUMPTION LAYER                                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│  │ AI Agent     │  │ LLM         │  │ Vector Store           │    │
│  │ (fine-tuned) │  │ (RAG)       │  │ (semantic search)      │    │
│  └──────────────┘  └──────────────┘  └────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Connector Interface

Each connector implements:

```java
interface DatabaseConnector {
    ConnectorType getType();                          // POSTGRESQL | COSMOS | ORACLE | MYSQL | MSSQL
    Connection connect(ConnectionConfig config);       // Returns authenticated connection
    List<TableSchema> discoverSchema();               // Introspect all tables/containers
    RawTableMetadata extractTableMetadata(String tableName);  // Extract DDL-level details
    long estimateRowCount(String tableName);          // Quick COUNT estimate
    void close();                                     // Cleanup resources
}
```

### Available Connectors

| Connector | Connection Type | Purpose | Tables |
|-----------|----------------|---------|--------|
| PostgresConnector | JDBC (IAM + SSL) | Primary transactional MMS | 38 tables |
| CosmosConnector | SDK (Primary Key) | Event store + audit + documents | 3 containers |
| OracleConnector | JDBC Thick (Wallet) | Legacy MRO data migration | Part master, vendor |
| MySQLConnector | JDBC (SSL) | Legacy tech log migration | Defect records |
| MSSQLConnector | JDBC (AD Auth) | ERP integration | Financial data |

---

## 3. Raw Metadata Extractor Output

Extracts per table/container directly from the database system catalogs. Keys:
- Column names, data types, max lengths, nullability
- Primary key columns
- Foreign keys (referencing table + column)
- Indexes (unique/full/composite)
- CHECK constraints and ENUM values
- Table/column comments (if any)
- Row count estimates

Output file: `raw_metadata.json` (see `04_enriched_metadata_schema.json` for full example)

---

## 4. Enricher Stages

### Stage 1: Name Enrichment
- `tail_number` → "Tail Number / Registration"
- `visit_reference` → "Visit Reference Number"
- Uses: NLP parser + camelCase/snake_case splitter + domain prefix rules

### Stage 2: Domain Mapping
- Matches tables to TOGAF domains using the `mro_features.json` definitions
- Sets `data_criticality` based on domain (Maintenance Execution = critical)
- Rule: `IF table_name LIKE '%llp%' OR '%life_limited%' THEN domain = 'Reliability', criticality = 'critical', safety = true`

### Stage 3: Relationship Discovery
- Parses all FK constraints into `enriched_relationship` entries
- Adds `business_meaning` to each relationship based on table semantics
- Discovers implicit cross-database relationships (e.g., visit_id in Postgres ↔ same event in Cosmos)

### Stage 4: Glossary & Compliance
- Matches table/column names against the domain glossary
- Attaches regulatory references (EASA/FAA/ICAO)
- Tags: AOG, CRS, MEL, LLP, AD, SB, etc.

### Stage 5: Use Case & Process Generation
- Reads process definitions and maps to endpoint calls
- Generates use cases from common scenarios (AOG, C-check planning, AD compliance)
- Populates `agent_training_notes` with behavioral guidance

### Stage 6: Decision & Alert Generation
- Generates decision trees from business rules
- Maps alert thresholds (LLP 50/90/100%) to database queries
- Documents escalation paths

---

## 5. Enriched JSON Output Sections (11 entity types)

| # | Entity Type | Description | Required for Agent? |
|---|-------------|-------------|---------------------|
| 1 | `enriched_table` | DB table with business context, columns, relationships, sample queries | YES |
| 2 | `enriched_column` | Column with business meaning, enum expansions, sensitivity | YES |
| 3 | `enriched_relationship` | FK + implicit business relationships | YES |
| 4 | `enriched_endpoint` | API endpoint with business rules, side effects, roles | YES |
| 5 | `enriched_process` | End-to-end business process with steps, KPIs, system actions | YES |
| 6 | `enriched_glossary` | Domain dictionary (AOG, CRS, MEL, LLP, AD, SB...) | YES |
| 7 | `enriched_usecase` | Concrete scenarios with trigger → steps → success criteria | YES |
| 8 | `enriched_stakeholder` | Roles, responsibilities, data access, typical queries | YES |
| 9 | `enriched_compliance` | Regulations mapping to entities, endpoints, audit needs | YES |
| 10 | `enriched_decision_rule` | Business decision trees with approval matrices | Recommended |
| 11 | `enriched_alert` | Alert definitions with severity escalation | Recommended |

---

## 6. AI Agent Training Strategy

```
enriched_metadata.json
    │
    ├──→ Agent learns TABLE STRUCTURE (what data exists, what it means)
    │     e.g. "life_limited_part" table has: remaining_life, total_life, part_serial
    │
    ├──→ Agent learns BUSINESS CONTEXT (why this data matters)
    │     e.g. LLP expiry = ground aircraft, regulatory risk, safety hazard
    │
    ├──→ Agent learns ENDPOINT CAPABILITIES (what actions are possible)
    │     e.g. POST /records/crs/generate = sign aircraft back to service
    │
    ├──→ Agent learns PROCESSES (how things flow end-to-end)
    │     e.g. C-check = induct → assign → execute → inspect → sign off
    │
    └──→ Agent learns DECISIONS & ALERTS (when to act, what to say)
          e.g. AOG = emergency escalation, 2-hour urgency
```

---

## 7. File Output Structure

```
horizon_airlines/_pre_planning_togaf/
├── mro_features.json                                 # Stage 1: Features
├── 02_api_design.md                                  # Stage 1: API design
├── 03_quarkus_implementation.md                      # Stage 1: Quarkus code
├── MMS_Complete_Package.md                           # Stage 1: Complete reference
│
├── 04_connector_parser_architecture.md               # Stage 2: This document
└── 04_enriched_metadata_schema.json                  # Stage 2: Enriched schema + example
```
