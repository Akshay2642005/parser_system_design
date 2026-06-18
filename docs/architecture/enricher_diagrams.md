# enricher_pipeline_diagram.md
# Copy this file content into: https://mermaid.live/ OR any Mermaid renderer

## C4 Context Diagram (Level 1)

```mermaid
C4Context
    title System Context — MMS Enricher

    Person(developer, "AI Agent Developer", "Consumes enriched metadata for agent training")
    
    System_Ext(postgres, "PostgreSQL (38 tables)", "Transactional MMS database")
    System_Ext(cosmos, "Cosmos DB (3 containers)", "Events, audit, documents")
    System_Ext(features, "mro_features.json", "Business feature definitions")
    System_Ext(api_spec, "02_api_design.md", "API specification")

    System_Boundary(enricher, "MMS Parser (Enricher)") {
        Container(extractor, "Raw Extractor", "Python", "Extracts raw schema metadata from DB")
        Container(pipeline, "Enrichment Pipeline", "Python", "6-stage enrichment process")
        Container(assembler, "Output Assembler", "Python", "Validates and writes enriched JSON")
    }

    System_Ext(agent, "AI Agent", "Fine-tuned on enriched metadata")
    System_Ext(vector, "Vector Store", "Semantic search index")

    Rel(extractor, postgres, "JDBC query", "Schema discovery")
    Rel(extractor, cosmos, "SDK query", "Container discovery")
    Rel(pipeline, extractor, "Reads", "raw_metadata.json")
    Rel(pipeline, features, "Reads", "Feature + reason mappings")
    Rel(pipeline, api_spec, "Reads", "Endpoint definitions")
    Rel(assembler, pipeline, "Assembles", "Enriched context")
    Rel(agent, assembler, "Consumes", "enriched_metadata.json")
    Rel(vector, assembler, "Indexes", "enriched_metadata.json")
    Rel(developer, agent, "Trains", "Fine-tuning pipeline")
```

## 6-Stage Pipeline Detail

```mermaid
flowchart LR
    subgraph Input[INPUT LAYER]
        R[raw_metadata.json]:::input
        F[mro_features.json]:::input  
        A[api_spec.yaml]:::input
        Y[rule YAML files]:::input
    end

    subgraph Stages[ENRICHMENT PIPELINE — 6 STAGES]
        direction TB
        S1[Stage 1<br/>Name Enrichment<br/>snake_case → Business Name]:::stage
        S2[Stage 2<br/>Feature & Reason Mapping<br/>Feature + Domain + Criticality]:::stage
        S3[Stage 3<br/>Relationship Discovery<br/>FK → Business Meaning]:::stage
        S4[Stage 4<br/>Process & Endpoint Mapping<br/>key_processes + endpoints]:::stage
        S5[Stage 5<br/>Glossary & Compliance Tagging<br/>Terms + Regulatory Ref]:::stage
        S6[Stage 6<br/>Use Case & Decision Generation<br/>Scenarios + Rules + Alerts]:::stage
    end

    subgraph Output[OUTPUT LAYER]
        E[enriched_metadata.json]:::output
        V[validation_report.json]:::output
    end

    R --> S1
    F --> S2
    Y --> S1
    Y --> S2
    Y --> S3
    Y --> S4
    A --> S4
    Y --> S5
    Y --> S6
    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> E
    E --> V

    classDef input fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef stage fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef output fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
```

## Enriched JSON Entity Types

```mermaid
mindmap
  root((Enriched Metadata))
    ::icon(fa fa-database)
    enriched_table
      feature
      reason
      business_name
      domain
      data_criticality
      key_processes
      endpoints
      enriched_columns
      relationships
      sample_queries
      glossary_tags
    enriched_endpoint
      http_method
      path
      business_name
      feature
      reason
      use_case
      related_tables
      business_rules
      auth
    enriched_process
      process_name
      feature
      reason
      steps
        system_actions
        performed_by
        business_rules
      kpi_metrics
      entity_dependencies
    enriched_glossary
      term
      acronym_of
      definition
      category
      reason
      regulatory_reference
      agent_notes
    enriched_usecase
      use_case_name
      feature
      reason
      trigger
      actors
      steps
      related_endpoints
      related_tables
      escalation_condition
      agent_training_notes
    enriched_stakeholder
      role
      department
      responsibilities
      data_access
      typical_queries
    enriched_compliance
      regulation
      title
      affected_entities
      affected_endpoints
      audit_requirements
    enriched_decision_rule
      decision_name
      input_conditions
      approval_rules
        auto_approve
        required_role
    enriched_alert
      alert_name
      severity_levels
        threshold_pct
        action
        notification_roles
      affected_query
```

## Data Flow Per Entity

```mermaid
stateDiagram-v2
    [*] --> RawTable: Extractor reads DB catalog
    RawTable --> NamedTable : Stage 1 — Name Enrichment
    NamedTable --> FeatureTable : Stage 2 — Feature & Reason Mapping
    FeatureTable --> RelationalTable : Stage 3 — Relationship Discovery
    RelationalTable --> MappedTable : Stage 4 — Process & Endpoint Mapping
    MappedTable --> TaggedTable : Stage 5 — Glossary & Compliance Tagging
    TaggedTable --> CompleteTable : Stage 6 — Use Case & Decision Gen
    CompleteTable --> [*] : Output Assembler writes JSON

    note right of RawTable
        Columns: name, type, pk, fk, 
        nullable, enum, comment
    end note
    
    note right of NamedTable
        Added: business_name, description
    end note
    
    note right of FeatureTable
        Added: feature, reason, domain, 
        criticality, regulatory_refs
    end note
    
    note right of RelationalTable
        Added: for each FK → 
        business_meaning
    end note
    
    note right of MappedTable
        Added: key_processes, endpoints, 
        sample_agent_queries
    end note
    
    note right of TaggedTable
        Added: glossary_tag references, 
        compliance tags
    end note

    note right of CompleteTable
        All enriched fields populated.
        Ready for output assembly.
    end note
```

## Rule Engine Flow

```mermaid
flowchart TD
    subgraph RuleEngine[RULE ENGINE]
        RE[RuleEngine.match()]:::rule
        R1{Exact match?}:::decision
        R2{Regex match?}:::decision
        R3{Wildcard match?}:::decision
        Default[Use default value]:::default
        Result[Return matched rule]:::result
    end

    Input[Raw name: life_limited_part] --> RE
    RE --> R1
    R1 -- Yes --> Result
    R1 -- No --> R2
    R2 -- Yes --> Result
    R2 -- No --> R3
    R3 -- Yes --> Result
    R3 -- No --> Default

    classDef rule fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef default fill:#fce4ec,stroke:#c62828,stroke-width:2px
    classDef result fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
```

## Deployment Architecture

```mermaid
flowchart LR
    subgraph CI[CI/CD Pipeline]
        PR[Schema Change PR] --> GA[GitHub Actions]
        GA --> Build[Docker Build]
        Build --> Push[Push to Registry]
    end

    subgraph K8s[Kubernetes]
        Init[Init: git-sync rules] --> Pod[Enricher Pod]
        Pod --> Output[enriched_metadata.json]
    end

    subgraph Storage[Storage Layer]
        Output --> S3[S3 / Blob Storage]
        S3 --> Agent[AI Agent Pipeline]
        S3 --> Vector[Vector Store]
    end

    Push --> K8s
```

## Single enriched_table JSON Structure

```mermaid
classDiagram
    class EnrichedTable {
        +String entity_id
        +String source_table
        +String source_database
        +String business_name
        +String business_description
        +Feature feature
        +String reason
        +String domain
        +String data_criticality
        +String[] stakeholders
        +String[] key_processes
        +Endpoint[] endpoints
        +EnrichedColumn[] columns
        +String[] primary_key
        +EnrichedRelationship[] foreign_key_relationships
        +SampleQuery[] sample_agent_queries
    }
    
    class Feature {
        +String function_name
        +String feature_name
        +String description
        +String reason
    }
    
    class EnrichedColumn {
        +String column_name
        +String business_name
        +String description
        +String reason
        +String data_type
        +Boolean is_safety_critical
        +EnumValue[] enum_values
        +String[] data_quality_rules
        +String agent_notes
    }
    
    class EnrichedRelationship {
        +String source_column
        +String target_table
        +String target_column
        +String relationship_type
        +String business_meaning
    }
    
    class Endpoint {
        +String method
        +String path
        +String purpose
        +String use_case
    }

    EnrichedTable *-- Feature
    EnrichedTable *-- EnrichedColumn
    EnrichedTable *-- EnrichedRelationship
    EnrichedTable *-- Endpoint
```
