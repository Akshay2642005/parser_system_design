# Metadata Enrichment Engine

Production-grade Python service that converts database metadata text files and database configuration files into a rich, AI-ready JSON representation.

## Purpose

Create semantic context from database schemas so downstream LLMs can understand databases, business entities, relationships, compliance concerns, use cases, and operational insights.

## Architecture

```
Config Files + Metadata TXT Files
          ↓
    Metadata Parser
          ↓
    Raw Metadata Model (Pydantic)
          ↓
    Enrichment Pipeline
      ├── Stage 1: Name Enrichment
      ├── Stage 2: Domain Mapping
      ├── Stage 3: Relationship Discovery
      ├── Stage 4: Glossary Generation
      ├── Stage 5: Compliance Classification
      ├── Stage 6: Use Case Generation
      ├── Stage 7: Process Discovery
      └── Stage 8: Alert Generation
          ↓
    Enriched Metadata JSON
```

## Project Structure

```
metadata_enrichment_engine/
├── src/
│   ├── parser/
│   │   ├── txt_parser.py          # Parse metadata TXT files
│   │   └── config_loader.py       # Load YAML config
│   ├── models/
│   │   └── metadata.py            # Pydantic models
│   ├── enrichers/
│   │   ├── name_enricher.py       # Stage 1: Business names
│   │   ├── domain_mapper.py       # Stage 2: Domain inference
│   │   ├── relationship_discovery.py  # Stage 3: Implicit relationships
│   │   ├── glossary_generator.py  # Stage 4: Business glossary
│   │   ├── compliance_classifier.py   # Stage 5: PII/PHI/PCI
│   │   ├── usecase_generator.py   # Stage 6: Use cases
│   │   ├── process_discovery.py   # Stage 7: Business processes
│   │   └── alert_generator.py     # Stage 8: Schema quality alerts
│   ├── pipeline/
│   │   └── enrichment_pipeline.py # Orchestration
│   ├── output/
│   │   └── json_serializer.py     # JSON serialization
│   └── cli.py                     # CLI entry point
├── tests/
├── samples/
│   ├── config.yaml
│   ├── clinic_db.txt
│   └── enriched_output_sample.json
├── pyproject.toml
└── README.md
```

## Installation

```bash
cd metadata_enrichment_engine
pip install -e ".[dev]"
```

## Usage

### CLI

```bash
# Basic usage — outputs to stdout
meta-enrich samples/clinic_db.txt

# With config and output file
meta-enrich samples/clinic_db.txt -c samples/config.yaml -o output.json

# Process a directory of TXT files
meta-enrich ./metadata_files/ -c config.yaml -o enriched.json

# Verbose logging
meta-enrich samples/clinic_db.txt -v
```

### Python API

```python
from src.pipeline.enrichment_pipeline import enrich_metadata

result = enrich_metadata(
    metadata_txt_path="samples/clinic_db.txt",
    config_path="samples/config.yaml",
    output_path="output.json",
)

# result is a dict with the enriched JSON
print(result["databases"][0]["domains"])
```

## Output Structure

```json
{
  "databases": [
    {
      "database_info": { "name": "...", "type": "..." },
      "tables": [...],
      "relationships": [...],
      "inferred_relationships": [...],
      "domains": [{ "domain": "Healthcare", "confidence": 0.93 }],
      "business_glossary": [{ "term": "...", "definition": "..." }],
      "classifications": [{ "column": "...", "classification": "PII" }],
      "use_cases": [{ "name": "...", "description": "..." }],
      "business_processes": [{ "process": "...", "tables_involved": [...] }],
      "alerts": [{ "severity": "HIGH", "message": "..." }],
      "recommendations": ["..."],
      "business_names": [{ "technical_name": "...", "business_name": "..." }]
    }
  ]
}
```

## Enrichment Stages

| Stage | Enricher | Description |
|-------|----------|-------------|
| 1 | Name Enricher | Converts technical names to business-friendly names |
| 2 | Domain Mapper | Infers business domain from table/column names |
| 3 | Relationship Discovery | Finds implicit relationships via shared columns |
| 4 | Glossary Generator | Creates business glossary entries |
| 5 | Compliance Classifier | Identifies PII, PHI, PCI, sensitive data |
| 6 | Use Case Generator | Infers likely use cases |
| 7 | Process Discovery | Discovers business workflows |
| 8 | Alert Generator | Flags schema quality issues |

## Running Tests

```bash
pytest
```

## Extensibility

### Adding a New Enrichment Stage

1. Create `src/enrichers/my_new_enricher.py`:

```python
from src.models.metadata import EnrichedDatabase, RawMetadata

def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """My custom enrichment logic."""
    # Read from metadata, write to enriched
    pass
```

2. Register in `src/pipeline/enrichment_pipeline.py`:

```python
from src.enrichers import my_new_enricher

STAGES = [
    # ... existing stages
    ("my_new_stage", my_new_enricher.enrich),
]
```

3. Add any new Pydantic models to `src/models/metadata.py`.

That's it — the pipeline automatically runs all registered stages in order.
