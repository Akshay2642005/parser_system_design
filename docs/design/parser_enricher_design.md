# MMS Parser (Enricher) — System Design Document

| Document Owner | MMS Data Engineering Team |
|---|---|
| Version | 1.0 |
| Status | Draft for Review |
| Date | 2026-06-18 |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [System Architecture Diagram](#2-system-architecture-diagram)
3. [Input Layer](#3-input-layer)
4. [Processing Layer (6-Stage Pipeline)](#4-processing-layer)
5. [Output Layer](#5-output-layer)
6. [Component Breakdown](#6-component-breakdown)
7. [Data Flow Specification](#7-data-flow-specification)
8. [Rule Engine Configuration](#8-rule-engine-configuration)
9. [Error Handling & Observability](#9-error-handling--observability)
10. [Tech Stack Recommendations](#10-tech-stack-recommendations)
11. [Extensibility Design](#11-extensibility-design)
12. [Deployment Architecture](#12-deployment-architecture)

---

## 1. System Overview

### 1.1 Purpose

The **MMS Metadata Enricher** transforms raw database metadata (table schemas, column types, foreign keys) into a rich, business-contextualised semantic layer that AI agents can consume. It bridges the gap between technical database structures and the business language of airline MRO operations.

### 1.2 Business Problem

Raw database metadata is insufficient for AI agents:
- `life_limited_part.remaining_life` → meaningless to an agent without context
- The agent needs to know: "This is safety-critical. If <= 0 the aircraft is grounded."
- `aircraft.status = 'AOG'` → the agent must understand "This is an emergency escalation"

The enricher solves this by attaching: **feature, reason, key processes, endpoints, glossary terms, compliance references, use cases, and decision rules** to every schema element.

### 1.3 Key Design Goals

| Goal | Description |
|------|-------------|
| **Traceability** | Every enriched element links back to its raw source table/column |
| **Completeness** | An agent should never encounter a table or column it cannot understand |
| **Extensibility** | New databases, tables, and enrichment rules can be added without code changes |
| **Determinism** | Same input always produces same output (rule-based, not generative) |
| **Auditability** | Every enrichment decision can be explained (which rule fired, why) |

### 1.4 System Context (C4 Level 1)

```
┌─────────────────┐     ┌──────────────────────────────────────────────────────┐
│                 │     │               MMS PARSER (ENRICHER)                   │
│    External     │     │                                                       │
│   Data Sources  │     │  ┌──────────┐   ┌───────────────┐   ┌──────────────┐  │
│                 │     │  │ Connector│──▶│   Extractor   │──▶│  Enricher    │  │
│  ┌──────────┐   │     │  │  Layer   │   │(raw metadata) │   │(6 stages)    │  │
│  │PostgreSQL│───┼────▶│  └──────────┘   └───────────────┘   └──────┬───────┘  │
│  └──────────┘   │     │                                             │          │
│  ┌──────────┐   │     │              ┌──────────────────────────────┘          │
│  │ CosmosDB │───┼────▶│              ▼                                        │
│  └──────────┘   │     │     ┌──────────────────┐                              │
│  ┌──────────┐   │     │     │  Enriched JSON   │                              │
│  │   MRO    │───┼────▶│     │  (AI-Ready)      │                              │
│  │ Features │   │     │     └──────────────────┘                              │
│  └──────────┘   │     └──────────────────────────────────────────────────────┘
│  ┌──────────┐   │                         │
│  │ API Spec │───┼────▶                   │
│  └──────────┘   │                        ▼
│                 │               ┌──────────────────┐
│                 │               │   AI Agent       │
│                 │               │  Fine-Tuning     │
│                 │               │  + RAG Pipeline  │
│                 │               └──────────────────┘
└─────────────────┘
```

---

## 2. System Architecture Diagram

### 2.1 Container Diagram (C4 Level 2)

```
┌══════════════════════════════════════════════════════════════════════════════════┐
║                         MMS ENRICHER — CONTAINER DIAGRAM                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝

                              INPUT SOURCES
                    ┌─────────┐ ┌────────┐ ┌─────────┐ ┌───────┐
                    │PostgreSQL│ │CosmosDB│ │mro_    │ │API    │
                    │(38 tbls) │ │(3 cont)│ │features│ │Spec   │
                    │          │ │        │ │.json   │ │.md    │
                    └─────┬────┘ └───┬────┘ └────┬────┘ └──┬────┘
                          │          │            │         │
                          ▼          ▼            ▼         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       RAW METADATA EXTRACTOR                                     │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Schema Discovery Engine                                                   │  │
│  │  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐  │  │
│  │  │Table/Column│ │PK/FK      │ │Indexes & │ │Enum       │ │Statistics  │  │  │
│  │  │Discovery   │ │Discovery  │ │Constraints│ │Extraction │ │(row count) │  │  │
│  │  └────────────┘ └───────────┘ └──────────┘ └───────────┘ └────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  Output: raw_metadata.json (one JSON object per table/container)                 │
└───────────────────────────┬─────────────────────────────────────────────────────┘
                            │
                            ▼
┌══════════════════════════════════════════════════════════════════════════════════┐
║                      ENRICHER CORE — 6-STAGE PIPELINE                           ║
╚══════════════════════════════════════════════════════════════════════════════════╝

  ┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌─────────┐    ┌──────────┐
  │ STAGE 1  │    │  STAGE 2  │    │  STAGE 3  │    │  STAGE 4  │    │ STAGE 5 │    │ STAGE 6  │
  │  Name    │───▶│  Feature  │───▶│Relation-  │───▶│  Process  │───▶│Glossary │───▶│  Use     │
  │Enrichment│    │ & Reason  │    │  ship     │    │ & Endpoint│    │& Compl. │    │ Case &   │
  │          │    │  Mapping  │    │ Discovery │    │  Mapping  │    │ Tagging │    │Decision  │
  └────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └────┬────┘    └────┬─────┘
       │                │                │                │               │              │
       │  Adds:         │  Adds:         │  Adds:         │  Adds:        │  Adds:       │  Adds:
       │  business_name │  feature       │  business_     │  key_processes│  definitions │  trigger→step
       │  description   │  reason        │  meaning       │  endpoints[]  │  regulatory  │  →escalation
       │                │  domain        │  per FK        │               │  references  │  decision trees
       └────────────────┴────────────────┴────────────────┴───────────────┴──────────────┴─────────────┘
                                                                                                      │
                            ┌────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              ENRICHED METADATA ASSEMBLER                                              │
│  ┌──────────────┐ ┌──────────────────┐ ┌─────────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │enriched_table│ │enriched_endpoint │ │enriched_process │ │enriched_     │ │enriched_usecase      │  │
│  │(1 per table) │ │(1 per endpoint)  │ │(1 per process)  │ │glossary/     │ │(1 per scenario)      │  │
│  │              │ │                  │ │                 │ │decision/     │ │                      │  │
│  │              │ │                  │ │                 │ │stakeholder   │ │                      │  │
│  └──────────────┘ └──────────────────┘ └─────────────────┘ └──────────────┘ └──────────────────────┘  │
└───────────────────────────────────┬──────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT LAYER                                                             │
│                                                                                                      │
│  ┌────────────────────────────────────────────────┐  ┌───────────────────────────────────────────┐   │
│  │ enriched_metadata.json                          │  │ enriched_metadata_schema.json             │   │
│  │ The actual data (N instances of each entity)   │  │ The schema definition (what fields exist) │   │
│  │                                                 │  │                                           │   │
│  │ Consumed by:                                    │  │ Consumed by:                              │   │
│  │  - AI Agent fine-tuning pipeline                │  │  - Validation of output                   │   │
│  │  - LLM RAG (vector store embedding)             │  │  - Downstream tool builders               │   │
│  │  - Semantic search indexing                     │  │  - Documentation generation               │   │
│  └────────────────────────────────────────────────┘  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stage Detail Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                   ENRICHMENT PIPELINE — STAGE DETAIL             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT TABLE: aircraft                                           │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ Raw: { "table_name": "aircraft", "columns": [          │      │
│  │   {"name":"tail_number","type":"varchar","pk":false},  │       │
│  │   {"name":"status","type":"varchar","enum":[...]}      │       │
│  │ ]}                                                     │       │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                  │
│  STAGE 1 [Name Enrichment] ─────────────────────────────────     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Rule: snake_case → business name                        │     │
│  │ "tail_number" → "Tail Number / Registration"            │     │
│  │ Input: raw column name                                  │     │
│  │ Source: name_rules.yaml dictionary                      │     │
│  │ Output: { ..., "business_name":"Tail Number/Reg", ... } │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  STAGE 2 [Feature & Reason Mapping] ───────────────────────     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Rule: table_name → mro_features.json index              │     │
│  │ "aircraft" → feature: "Maintenance Visit Forecasting"   │     │
│  │               reason: "Root entity of the entire MMS..."│     │
│  │ Source: feature_rules.yaml + mro_features.json          │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  STAGE 3 [Relationship Discovery] ─────────────────────────     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Rule: FK constraints → business meaning                 │     │
│  │ aircraft.model_id → aircraft_model.model_id             │     │
│  │ business_meaning: "An aircraft has exactly 1 model"    │     │
│  │ Source: FK metadata + relationship_templates.yaml       │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  STAGE 4 [Process & Endpoint Mapping] ─────────────────────     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Rule: entity → process_maps.yaml                        │     │
│  │ key_processes: ["Aircraft Induction","Visit Planning",  │     │
│  │                 "Lease Return","Fleet Status Monitor"]   │     │
│  │ endpoints: ["GET /aircraft","GET /aircraft/{id}"]      │     │
│  │ Source: process_maps.yaml + API spec                    │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  STAGE 5 [Glossary & Compliance Tagging] ─────────────────     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Rule: keyword match → glossary.yaml + compliance.yaml   │     │
│  │ Matches: "life_limited_part" → gls: "LLP"              │     │
│  │                         → reg: "EASA Part 21.A.307"    │     │
│  │ Source: glossary.yaml, compliance.yaml                  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  STAGE 6 [Use Case & Decision Generation] ────────────────     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Rule: entity + process → use_case templates             │     │
│  │ "AOG parts sourcing" use case generated from:           │     │
│  │   table: rotable_component                              │     │
│  │   process: AOG Response                                 │     │
│  │   endpoint: GET /inventory/rotables                     │     │
│  │ Source: use_case_templates.yaml, decision_trees.yaml    │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  OUTPUT: enriched_table containing ALL enriched fields           │
│  "business_name","feature","reason","key_processes",            │
│  "endpoints","columns[enriched]","relationships",               │
│  "glossary_tags","regulatory_refs","sample_queries"             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Input Layer

### 3.1 Raw Metadata Schema (from Extractor)

```json
{
  "extraction_meta": {
    "extracted_at": "2026-06-18T10:00:00Z",
    "database_type": "postgresql",
    "database_name": "mms",
    "schema": "public",
    "connector_version": "1.0.0",
    "total_tables": 38,
    "total_views": 2
  },
  "tables": [
    {
      "table_name": "aircraft",
      "table_type": "TABLE",
      "row_count_estimate": 120,
      "columns": [
        {
          "column_name": "aircraft_id",
          "ordinal_position": 1,
          "data_type": "uuid",
          "is_nullable": false,
          "is_primary_key": true,
          "is_foreign_key": false,
          "fk_references": null,
          "enum_values": null,
          "comment": "Primary key"
        }
      ],
      "primary_key": {"columns": ["aircraft_id"]},
      "foreign_keys": [...],
      "indexes": [...]
    }
  ],
  "views": [...]
}
```

### 3.2 Supporting Inputs

| Input | Format | Source | Purpose |
|-------|--------|--------|---------|
| `mro_features.json` | JSON | Business Architecture | Business function + feature definitions with reasons |
| `02_api_design.md` | Markdown | API Design Team | Full endpoint definitions with use cases |
| `04_enriched_metadata_schema.json` | JSON | This design | Schema rules for each entity type |
| `name_rules.yaml` | YAML | Domain Dictionary | snake_case → business name mappings |
| `feature_rules.yaml` | YAML | Business Architecture | table/column → feature mapping rules |
| `process_maps.yaml` | YAML | Process Engineering | End-to-end process definitions with step→endpoint mapping |
| `glossary.yaml` | YAML | Domain SME | Technical terms, acronyms, definitions |
| `compliance.yaml` | YAML | Regulatory | EASA/FAA/ICAO regulation→entity mapping |
| `decision_trees.yaml` | YAML | Business Rules | Decision logic with approval matrices |
| `use_case_templates.yaml` | YAML | AI Training Team | Scenario templates for agent training |

---

## 4. Processing Layer (6-Stage Pipeline)

### 4.1 Pipeline Orchestration

The pipeline is a sequential DAG where each stage enriches a shared context object.

```
enrichment_context = {
    "raw_metadata": {...},     # Set by input loader
    "enriched_tables": [],     # Populated stage by stage
    "enriched_endpoints": [],
    "enriched_relationships": [],
    "enriched_processes": [],
    "enriched_glossary": [],
    "enriched_usecases": [],
    "enriched_decisions": [],
    "enriched_alerts": [],
    "enriched_compliance": [],
    "enriched_stakeholders": [],
    "errors": []               # Non-fatal errors collected per stage
}
```

### 4.2 Stage 1: Name Enrichment

| Property | Value |
|----------|-------|
| **Goal** | Convert technical column names to human-readable business names |
| **Input** | Raw table/column metadata |
| **Output** | Same structure + `business_name`, `business_description` |
| **Method** | Pattern matching + dictionary lookup + fallback NLP |

**Rules Engine Logic:**
```
for each column in table.columns:
    if column.name in name_dictionary:
        column.business_name = name_dictionary[column.name].business_name
        column.description   = name_dictionary[column.name].description
    else if matches pattern (e.g. "has_*", "*_id", "*_pct"):
        apply pattern-based naming
    else:
        snake_case → Title Case (fallback)
        column.business_name = split_and_title(column.name)
```

**Name Dictionary Examples:**
| Raw Name | Business Name | Description |
|----------|---------------|-------------|
| `tail_number` | Tail Number / Registration | Aircraft registration mark displayed on fuselage |
| `aircraft_id` | Aircraft Identifier | System-generated UUID, internal key |
| `visit_reference` | Visit Reference Number | Human-readable code: MV-2026-0001 |
| `check_type` | Check Type | A/B/C/D check classification |
| `remaining_life` | Remaining Life | Flight cycles/hours/calendar remaining before mandatory removal |

### 4.3 Stage 2: Feature & Reason Mapping

| Property | Value |
|----------|-------|
| **Goal** | Attach business feature context and reason to every table and column |
| **Input** | Named-enriched metadata + `mro_features.json` |
| **Output** | Each table gets `feature` object, `reason`, `domain`, `data_criticality`, `regulatory_significance` |
| **Method** | Table name → feature mapping rules |

**Rules Engine Logic:**
```
for each table in context.enriched_tables:
    # 1. Map to feature
    matched_feature = feature_rules.match(table.source_table)
    table.feature = {
        "function_name": matched_feature.function_name,
        "feature_name": matched_feature.feature_name,
        "description": matched_feature.description,
        "reason": matched_feature.reason          # from mro_features.json
    }

    # 2. Generate entity-level reason
    table.reason = reason_templates.generate(
        table.source_table,
        table.feature,
        table.foreign_key_relationships
    )

    # 3. Assign domain
    table.domain = domain_rules.map(table.source_table)

    # 4. Assign criticality
    table.data_criticality = criticality_rules.evaluate(
        table.source_table,
        table.is_safety_critical,
        table.regulatory_significance
    )

    # 5. Attach regulatory references
    table.regulatory_significance = compliance_rules.lookup(table.source_table)
```

**Criticality Rules:**
| Condition | Criticality |
|-----------|-------------|
| Table is safety-related (LLP, AD, defect, CRS, aircraft status) | `safety_critical` |
| Table drives flight dispatch (aircraft, visit, engine) | `safety_critical` |
| Table manages high-value assets (rotables, inventory) | `business_critical` |
| Table supports planning/reference (check_package, station) | `operational` |
| Table is static reference data (aircraft_model, part_master) | `reference` |

### 4.4 Stage 3: Relationship Discovery

| Property | Value |
|----------|-------|
| **Goal** | Add business meaning to every foreign key relationship |
| **Input** | Raw FK constraints + enriched tables |
| **Output** | Each FK gets `business_meaning` describing the real-world link |
| **Method** | Template-based meaning generation from table names |

**Relationship Meaning Templates:**
```
"A {source_table} belongs to exactly one {target_table}"
    → e.g. "A task_card belongs to exactly one maintenance_visit"

"A {source_table} can have many {target_table}(s)"
    → e.g. "An aircraft can have many maintenance_visits"

"Each {source_table} references a {target_table} that defines its {column}"
    → e.g. "Each aircraft references an aircraft_model that defines its maintenance program"
```

### 4.5 Stage 4: Process & Endpoint Mapping

| Property | Value |
|----------|-------|
| **Goal** | Link each table to the business processes and API endpoints that use it |
| **Input** | Enriched tables + process_maps.yaml + API endpoint definitions |
| **Output** | Each table gets `key_processes[]` and `endpoints[]` |
| **Method** | Cross-reference mapping by entity involvement |

**Process Mapping:**
```
for each table in context.enriched_tables:
    for each process in process_maps:
        if table.source_table in process.entity_dependencies:
            table.key_processes.append(process.process_name)

    for each endpoint in api_spec:
        if table.source_table in endpoint.related_tables:
            table.endpoints.append({
                "method": endpoint.method,
                "path": endpoint.path,
                "purpose": endpoint.purpose,
                "use_case": endpoint.use_case
            })
```

### 4.6 Stage 5: Glossary & Compliance Tagging

| Property | Value |
|----------|-------|
| **Goal** | Tag tables/columns with domain glossary terms and regulatory references |
| **Input** | Enriched tables + glossary.yaml + compliance.yaml |
| **Output** | Each table gets `glossary_tags[]` and enriched columns get regulatory hints |
| **Method** | Keyword matching on names and descriptions |

**Keyword Matching Rules:**
```
for each table in context.enriched_tables:
    for each term in glossary:
        if term.name matches table.source_table (partial/full):
            table.glossary_tags.append(term)

    for each compliance_entry in compliance_rules:
        if table.source_table in compliance_entry.affected_entities:
            table.regulatory_significance.append(compliance_entry.regulation)
```

### 4.7 Stage 6: Use Case & Decision Generation

| Property | Value |
|----------|-------|
| **Goal** | Generate concrete scenarios and decision trees the AI agent will encounter |
| **Input** | All previous enriched data + use_case_templates.yaml + decision_trees.yaml |
| **Output** | `enriched_usecase[]`, `enriched_decision_rule[]`, `enriched_alert[]` |
| **Method** | Template instantiation with entity references |

**Use Case Generation Template:**
```
AOG_Parts_Sourcing:
    uses_tables: [rotable_component, part_master, aircraft, vendor]
    uses_endpoints: [GET /inventory/rotables, POST /inventory/rotables/{id}/move]
    trigger_condition: "aircraft.status == 'AOG'"
    generates:
        entity_id: "uc_aog_parts_sourcing"
        feature: matched from table.feature
        reason: "Every hour of AOG costs $10K-$150K..."
        steps: [check_own_stock, check_other_station, check_vendor, escalate]
```

---

## 5. Output Layer

### 5.1 Enriched Metadata JSON Structure

```json
{
  "schema_version": "enriched_metadata_v2",
  "enricher_name": "MMS Metadata Enricher v1.0",
  "enriched_at": "2026-06-18T10:00:00Z",
  "source_system": "Airline Maintenance Management System",
  "pipeline_run": {
    "started_at": "2026-06-18T10:00:00Z",
    "completed_at": "2026-06-18T10:02:34Z",
    "duration_seconds": 154,
    "stages_completed": 6,
    "tables_enriched": 38,
    "endpoints_enriched": 62,
    "relationships_enriched": 84,
    "use_cases_generated": 12,
    "errors": [],
    "warnings": 3
  },
  "sections": {
    "tables": [ /* 38 enriched_table objects */ ],
    "endpoints": [ /* 62 enriched_endpoint objects */ ],
    "processes": [ /* 5 enriched_process objects */ ],
    "glossary": [ /* 45 enriched_glossary objects */ ],
    "use_cases": [ /* 12 enriched_usecase objects */ ],
    "stakeholders": [ /* 6 enriched_stakeholder objects */ ],
    "compliance": [ /* 8 enriched_compliance objects */ ],
    "decisions": [ /* 10 enriched_decision_rule objects */ ],
    "alerts": [ /* 7 enriched_alert objects */ ]
  }
}
```

### 5.2 Single enriched_table Output (Compact Form)

```json
{
  "entity_id": "tab_maintenance_visit",
  "entity_type": "enriched_table",
  "source_table": "maintenance_visit",
  "source_database": "postgresql",
  "business_name": "Maintenance Visit Record",
  "feature": {
    "function_name": "Aircraft Maintenance Planning & Scheduling",
    "feature_name": "Maintenance Program Check Management",
    "reason": "Ensures each aircraft adheres to manufacturer-approved programs"
  },
  "reason": "The maintenance visit is the central organizing entity...",
  "domain": "Maintenance Execution",
  "data_criticality": "safety_critical",
  "key_processes": [
    "Check Scheduling",
    "Visit Execution",
    "CRS Generation",
    "Maintenance Cost Accrual"
  ],
  "endpoints": [
    {"method": "GET", "path": "/visits", "purpose": "List all visits"},
    {"method": "POST", "path": "/visits", "purpose": "Create new visit"},
    {"method": "POST", "path": "/visits/{id}/start", "purpose": "Start visit"}
  ],
  "columns": [ /* enriched_column[] */ ],
  "foreign_key_relationships": [ /* enriched_relationship[] */ ],
  "sample_agent_queries": [ /* SQL examples */ ]
}
```

### 5.3 Output Consumers

| Consumer | Use | Format Required |
|----------|-----|-----------------|
| AI Agent Fine-Tuning | Training data for domain-specific agent | Full enriched JSON |
| LLM RAG Pipeline | Context injection for question-answering | Chunked enriched JSON |
| Vector Store (Semantic Search) | Embedding + retrieval | Flattened key-value pairs |
| Documentation Generator | Human-readable schema docs | JSON → Markdown |
| Validation Pipeline | Schema compliance checks | Against schema JSON |

---

## 6. Component Breakdown

### 6.1 Module Architecture

```
enricher/
│
├── main.py                        # Entry point, CLI argument parsing
├── pipeline.py                    # Pipeline orchestrator (stage sequencer)
│
├── input/
│   ├── raw_metadata_loader.py     # Reads raw_metadata.json
│   ├── features_loader.py         # Reads mro_features.json
│   ├── api_spec_loader.py         # Parses API spec (YAML/Markdown)
│   └── rule_loader.py             # Loads all YAML rule files
│
├── stages/
│   ├── stage1_name_enrichment.py  # Name dictionary + NLP
│   ├── stage2_feature_mapping.py  # Feature + reason + domain + criticality
│   ├── stage3_relationship.py     # Business meaning for FKs
│   ├── stage4_process_map.py      # Process + endpoint linking
│   ├── stage5_glossary.py         # Glossary + compliance tagging
│   └── stage6_usecase_gen.py      # Use case + decision + alert generation
│
├── rules/
│   ├── name_dictionary.yaml       # Technical → business name mapping
│   ├── feature_rules.yaml         # Table → feature mapping
│   ├── domain_rules.yaml          # Table → TOGAF domain mapping
│   ├── relationship_templates.yaml # FK → business meaning templates
│   ├── process_maps.yaml          # Process definitions
│   ├── glossary.yaml              # Domain dictionary
│   ├── compliance.yaml            # Regulatory references
│   ├── decision_trees.yaml        # Business decision logic
│   └── use_case_templates.yaml    # Scenario templates
│
├── output/
│   ├── enriched_assembler.py      # Assembles final JSON output
│   ├── enriched_validator.py      # Validates against schema
│   └── enriched_exporter.py       # Exports to various formats
│
├── shared/
│   ├── models.py                  # Dataclasses for all entity types
│   ├── enrichment_context.py      # Shared context object
│   ├── error_handler.py           # Error collection + reporting
│   └── logger.py                  # Structured logging
│
├── tests/
│   ├── test_pipeline.py
│   ├── test_stage1.py
│   ├── test_stage2.py
│   ├── fixtures/                  # Test data files
│   └── mock_rules/                # Test rule files
│
└── config.yaml                    # Pipeline configuration
```

### 6.2 Core Class Design

```python
class EnrichmentContext:
    """Thread-safe shared context passed through pipeline stages."""
    raw_metadata: RawMetadata
    enriched_tables: list[EnrichedTable]
    enriched_endpoints: list[EnrichedEndpoint]
    enriched_relationships: list[EnrichedRelationship]
    enriched_processes: list[EnrichedProcess]
    enriched_glossary: list[EnrichedGlossary]
    enriched_usecases: list[EnrichedUseCase]
    enriched_decisions: list[EnrichedDecisionRule]
    enriched_alerts: list[EnrichedAlert]
    enriched_compliance: list[EnrichedCompliance]
    enriched_stakeholders: list[EnrichedStakeholder]
    errors: list[EnrichmentError]
    pipeline_meta: PipelineMetadata

class EnrichmentStage(ABC):
    """Base class for all enrichment stages."""
    stage_id: str
    dependencies: list[str]  # Stage IDs that must complete first

    @abstractmethod
    def execute(self, context: EnrichmentContext) -> None:
        """Execute stage logic. Mutates context in place."""
        pass

class PipelineOrchestrator:
    """Sequentially executes stages with dependency resolution."""
    stages: dict[str, EnrichmentStage]

    def run(self, context: EnrichmentContext) -> EnrichmentContext:
        for stage in self.stages.values():
            stage.execute(context)
        return context
```

---

## 7. Data Flow Specification

### 7.1 End-to-End Flow

```
Raw PostgreSQL Schema (INFORMATION_SCHEMA)
         │
         │ JDBC Query
         ▼
┌────────────────────────────────┐
│     RAW EXTRACTOR              │   Run: On schema change / scheduled
│  Reads system catalogs         │
│  Writes raw_metadata.json      │
└─────────────┬──────────────────┘
              │
              │ File Read
              ▼
┌────────────────────────────────┐
│     ENRICHER LAUNCHER          │   Run: On demand / CI trigger
│  1. Load raw_metadata.json     │
│  2. Load mro_features.json     │
│  3. Load API spec              │
│  4. Load all rule YAML files   │
│  5. Initialize context         │
└─────────────┬──────────────────┘
              │
              ▼
┌────────────────────────────────┐
│     STAGE 1: Name Enrichment   │   O(n) per column
│  For each table → each column: │
│  Look up name_dictionary.yaml  │
│  Apply pattern-based fallback  │
└─────────────┬──────────────────┘
              │
              ▼
┌────────────────────────────────┐
│     STAGE 2: Feature Mapping   │   O(n) per table
│  For each table:               │
│  Match feature_rules.yaml      │
│  Generate reason from template │
│  Assign domain + criticality   │
│  Attach regulatory references  │
└─────────────┬──────────────────┘
              │
              ▼
┌────────────────────────────────┐
│     STAGE 3: Relationships     │   O(n × m) FK pairs
│  For each FK in raw metadata:  │
│  Generate business_meaning     │
│  Create enriched_relationship  │
└─────────────┬──────────────────┘
              │
              ▼
┌────────────────────────────────┐
│     STAGE 4: Process Mapping   │   O(n × p) tables × processes
│  For each table:               │
│  Look up process_maps.yaml     │
│  Add matching key_processes[]  │
│  Look up api endpoints         │
│  Add matching endpoints[]      │
└─────────────┬──────────────────┘
              │
              ▼
┌────────────────────────────────┐
│     STAGE 5: Glossary Tagging  │   O(n × g) tables × glossary
│  For each table/column:        │
│  Keyword match glossary.yaml   │
│  Tag with term references      │
│  Match compliance.yaml         │
│  Tag with regulatory refs      │
└─────────────┬──────────────────┘
              │
              ▼
┌────────────────────────────────┐
│     STAGE 6: Use Case Gen      │   O(u) templates × matches
│  For each use case template:   │
│  If table dependencies match:  │
│  Instantiate enriched_usecase  │
│  Generate decision rules       │
│  Generate alert definitions    │
└─────────────┬──────────────────┘
              │
              ▼
┌────────────────────────────────┐
│     OUTPUT ASSEMBLER           │
│  Validate against schema       │
│  Write enriched_metadata.json  │
│  Write validation report       │
└─────────────┬──────────────────┘
              │
              ├──────────────────────────────┐
              ▼                              ▼
┌──────────────────────┐    ┌──────────────────────────┐
│  enriched_metadata   │    │  validation_report.json  │
│  .json               │    │  warnings, errors, stats │
│                      │    │                          │
│  → AI Agent training  │    │  → QA Review             │
│  → RAG pipeline       │    │  → Pipeline monitoring   │
└──────────────────────┘    └──────────────────────────┘
```

### 7.2 State Machine Per Entity

```
RAW TABLE ──▶ STAGE 1 ──▶ STAGE 2 ──▶ STAGE 3 ──▶ STAGE 4 ──▶ STAGE 5 ──▶ STAGE 6 ──▶ OUTPUT
  .name()      .business    .feature     .relation-   .key_process  .glossary    .use_case
  .type()      .name()      .reason()    .ships[]     .endpoints[]  .tags[]      .decisions[]
  .nullable()  .descr()     .domain()                .sample_q[]   .compliance
  .pk/fk                    .criticality                             .refs[]
```

---

## 8. Rule Engine Configuration

### 8.1 Rule File Format

Each rule file is a YAML document loaded at pipeline startup:

```yaml
# name_dictionary.yaml
columns:
  - raw_name: "tail_number"
    business_name: "Tail Number / Registration"
    description: "Aircraft registration mark displayed on the fuselage"
    patterns:
      format: "^[A-Z]-[A-Z0-9]{3,6}$"
      examples: ["G-EZAT", "N123AB", "D-AIBC"]

  - raw_name: "remaining_life"
    business_name: "Remaining Life"
    description: "Flight cycles/hours/calendar remaining before mandatory removal"
    is_safety_critical: true
    unit_suffix: true
    agent_hint: "If <= 0, the aircraft is grounded"
```

```yaml
# feature_rules.yaml
mappings:
  - table_pattern: "aircraft"
    function_name: "Aircraft Maintenance Planning & Scheduling"
    feature_name: "Maintenance Visit Forecasting Engine"
    domain: "Fleet Management"
    criticality: "safety_critical"
    stakeholders: ["Fleet Manager", "CAMO Engineer", "Flight Operations"]

  - table_pattern: "life_limited_part|llp"
    function_name: "Reliability & Airworthiness Monitoring"
    feature_name: "Life-Limited Part Monitoring"
    domain: "Reliability & Airworthiness"
    criticality: "safety_critical"
    regulatory: ["EASA Part 21.A.307", "FAA Part 39.7"]

  - table_pattern: "rotable_component"
    function_name: "Component & Inventory Control"
    feature_name: "Rotable & Repairable Pool Management"
    domain: "Inventory & Supply Chain"
    criticality: "business_critical"
```

```yaml
# process_maps.yaml
processes:
  - process_name: "C-Check Execution"
    description: "End-to-end C-check from induction to CRS"
    owner: "Hangar Manager"
    typical_duration_hours: 336
    entity_dependencies:
      - "aircraft"
      - "maintenance_visit"
      - "task_card"
      - "check_package"
      - "certificate_release"
    steps:
      - step: 1
        name: "Aircraft Induction"
        system_actions: ["POST /visits/{id}/start"]
        performed_by: ["Lead Mechanic"]
        hours: 4
      - step: 2
        name: "Task Card Assignment"
        system_actions: ["POST /planning/task-cards/{id}/assign"]
        performed_by: ["Hangar Supervisor"]
        hours: 2
      # ... more steps
```

### 8.2 Rule Evaluation Engine

```python
class RuleEngine:
    """Pattern-matching rule engine with priority ordering."""

    def __init__(self, rules: list[Rule]):
        self.rules = sorted(rules, key=lambda r: r.priority)

    def match(self, input_name: str, ruleset: str = "exact") -> Rule | None:
        """
        1. Try exact match first
        2. Try regex/pattern match
        3. Try wildcard match
        4. Return None if no match (logging warning)
        """
        for rule in self.rules:
            if rule.matches(input_name):
                return rule
        return None
```

---

## 9. Error Handling & Observability

### 9.1 Error Classification

| Category | Severity | Example | Pipeline Impact |
|----------|----------|---------|-----------------|
| Missing Rule | WARNING | Table "new_engine_type" has no feature mapping | Continue with partial enrichment |
| Invalid Input | ERROR | raw_metadata.json is malformed JSON | Halt pipeline |
| Schema Mismatch | WARNING | Column has unsupported data type | Skip column, continue |
| FK Orphan | WARNING | FK references non-existent table | Skip relationship, continue |
| Template Error | ERROR | Use case template has bad reference | Skip use case, continue |

### 9.2 Structured Logging

```json
{
  "timestamp": "2026-06-18T10:01:23Z",
  "level": "WARNING",
  "pipeline_id": "run_abc123",
  "stage": "stage2_feature_mapping",
  "entity": "table:new_engine_type",
  "message": "No feature mapping found for table 'new_engine_type'. Using default domain 'Operational'.",
  "suggestion": "Add mapping to feature_rules.yaml",
  "trace_id": "trace_xyz789"
}
```

### 9.3 Validation Report (Output Sidecar)

Generated alongside enriched metadata for QA:

```json
{
  "pipeline_run": {
    "id": "run_abc123",
    "started_at": "2026-06-18T10:00:00Z",
    "completed_at": "2026-06-18T10:02:34Z",
    "status": "COMPLETED_WITH_WARNINGS"
  },
  "summary": {
    "tables_input": 38,
    "tables_enriched": 38,
    "endpoints_mapped": 62,
    "relationships_discovered": 84,
    "use_cases_generated": 12,
    "glossary_tags_applied": 156,
    "errors": 0,
    "warnings": 3,
    "info": 12
  },
  "warnings": [
    {
      "stage": "stage2_feature_mapping",
      "entity": "table:new_engine_type",
      "message": "No feature mapping — using default",
      "severity": "LOW"
    },
    {
      "stage": "stage4_process_map",
      "entity": "table:pbh_contract",
      "message": "No process reference found",
      "severity": "MEDIUM"
    }
  ],
  "coverage": {
    "tables_with_feature": "100% (38/38)",
    "columns_with_business_name": "96% (412/429)",
    "tables_with_sample_queries": "58% (22/38)",
    "fks_with_business_meaning": "100% (84/84)"
  }
}
```

---

## 10. Tech Stack Recommendations

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Language | Python 3.12+ | Rich YAML/JSON parsing, ML ecosystem, agent-ready |
| Pipeline Framework | Apache Beam / Prefect / Airflow | For scheduled runs, dependency mgmt, observability |
| Configuration | YAML | Human-readable, version-control friendly |
| Data Model | Pydantic v2 | Type-safe dataclasses with validation |
| Testing | pytest + factory_boy | Test fixtures for each stage |
| Monitoring | Prometheus + Grafana | Pipeline metrics (duration, error rate, coverage) |
| Logging | structlog | Structured JSON logs for ELK/Loki |
| Validation | JSON Schema (Draft 2020-12) | Output contract validation |
| Containerisation | Docker | Portable execution |
| CI/CD | GitHub Actions | Trigger on schema change / rule change |

### Why Python over Java/Quarkus?

| Factor | Python | Java | Rationale |
|--------|--------|------|-----------|
| Rule iteration speed | Fast | Slow | Rules change frequently during SME review |
| YAML/JSON parsing | Native | Needs libraries | Primary I/O format |
| AI/ML integration | Excellent | Moderate | Agents consume output directly |
| Startup time | Instant | Seconds | Frequent CI runs |
| Schema evolution | Dynamic | Static | Tables added frequently |

The enricher is a **batch data transformation pipeline**, not a transactional API. Python's ecosystem is better suited for this pattern.

---

## 11. Extensibility Design

### 11.1 Adding a New Database

1. **Connector** implements `DatabaseConnector` interface → produces `raw_metadata.json`
2. **Name rules** add entries to `name_dictionary.yaml` for new table/column names
3. **Feature rules** add entries to `feature_rules.yaml` mapping new tables to existing features
4. **Process maps** update if new tables support existing processes

**No code changes to pipeline stages.** Only YAML configuration changes.

### 11.2 Adding a New Enrichment Stage

```python
class Stage7CustomEnrichment(EnrichmentStage):
    stage_id = "stage7_custom"
    dependencies = ["stage6_usecase_gen"]

    def execute(self, context: EnrichmentContext) -> None:
        # Custom logic that reads/writes context
        pass
```

Register in `pipeline.py`:
```python
PipelineOrchestrator(stages=[
    Stage1NameEnrichment(),
    Stage2FeatureMapping(),
    Stage3RelationshipDiscovery(),
    Stage4ProcessMapping(),
    Stage5GlossaryTagging(),
    Stage6UseCaseGen(),
    Stage7CustomEnrichment(),  # New
])
```

### 11.3 Adding a New Entity Type

1. Define dataclass in `shared/models.py`
2. Add field to `EnrichmentContext`
3. Create assembler logic in `output/enriched_assembler.py`
4. Add to JSON Schema in `enriched_metadata_schema.json`

---

## 12. Deployment Architecture

### 12.1 CI/CD Trigger

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Schema      │     │  GitHub Actions  │     │ Docker       │
│ Change PR   │────▶│  - Run enricher  │────▶│ Registry     │
│ (DDL)       │     │  - Validate      │     │ (image)      │
└─────────────┘     │  - Publish JSON  │     └──────────────┘
                    └────────┬─────────┘
                             │
                             ▼
┌──────────────────────────────────────────┐
│             OUTPUT ARTIFACTS             │
│                                          │
│  enriched_metadata.json  ────▶ S3/Blob  │
│  validation_report.json  ────▶ S3/Blob  │
│  enriched_metadata_schema.json ──▶ S3   │
└──────────────────────────────────────────┘
```

### 12.2 Runtime Environment

```
┌────────────────────────────────────────────────────────┐
│                    Kubernetes / Docker                  │
│                                                        │
│  ┌────────────────────────────────────────────┐        │
│  │  MMS Enricher Pod (Python 3.12)            │        │
│  │                                            │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │        │
│  │  │ Stage 1  │  │ Stage 2  │  │  ...     │ │        │
│  │  └──────────┘  └──────────┘  └──────────┘ │        │
│  └────────────────────────────────────────────┘        │
│                                                        │
│  InitContainers:                                       │
│  - git-sync: Clone rule YAML files from repo            │
│  - config-loader: Validate all input files             │
│                                                        │
│  Volumes:                                               │
│  - /rules: ConfigMap from rule YAML files              │
│  - /input: raw_metadata.json (init container)          │
│  - /output: enriched_metadata.json (persistent)        │
└────────────────────────────────────────────────────────┘
```

### 12.3 Execution Modes

| Mode | Trigger | When | SLA |
|------|---------|------|-----|
| Full | Schema change / Monthly | Batch all 38 tables | < 5 minutes |
| Incremental | New table added | Single table only | < 30 seconds |
| Rule-only | Rule YAML change | Re-run with cached raw metadata | < 30 seconds |
| Validation | PR creation | Dry-run with diff report | < 2 minutes |

---

## Appendix A: File Manifest

| File | Description |
|------|-------------|
| `04_parser_enricher_design.md` | This system design document |
| `04_enriched_metadata_schema.json` | Complete enriched JSON schema with example instances |
| `mro_features.json` | Business features (Stage 1 output) |
| `02_api_design.md` | API specification (referenced by enricher) |

## Appendix B: Key Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Rule-based (not LLM-based) enrichment | Determinsitic, auditable, version-controllable. LLMs would introduce hallucination and non-determinism. |
| 2 | YAML for rules, not code | Domain SMEs can review and modify without engineering. Changes don't require deployments. |
| 3 | Single JSON output file | Agents and downstream pipelines prefer a single artifact over multiple files. |
| 4 | Python over Java | The enricher is a batch transformation pipeline, not a transactional API. Python's ecosystem (YAML, JSON, Pydantic) is superior for this pattern. |
| 5 | Pipeline stages are sequential, not parallel | Each stage depends on the previous. Parallelisation within a stage (per-table) is possible but unnecessary at this scale (38 tables). |
| 6 | Warnings do not halt pipeline | Partial enrichment is better than no enrichment. A missing rule for one table shouldn't block the other 37. |
