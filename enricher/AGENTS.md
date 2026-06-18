# AGENTS.md — MMS Enricher (Python)

This is the Python 3.12 implementation of the MMS Metadata Enricher — a batch transformation pipeline that turns raw database metadata into enriched JSON for AI agent consumption.

---

## State

| Item | Status |
|------|--------|
| `rules/name_dictionary.yaml` | ✅ Written (10 tables) |
| `rules/feature_rules.yaml` | ❌ |
| `rules/domain_rules.yaml` | ❌ |
| `rules/relationship_templates.yaml` | ❌ |
| `rules/process_maps.yaml` | ❌ |
| `rules/glossary.yaml` | ❌ |
| `rules/compliance.yaml` | ❌ |
| `rules/decision_trees.yaml` | ❌ |
| `rules/use_case_templates.yaml` | ❌ |
| `stages/` module | ❌ |
| `input/` module | ❌ |
| `output/` module | ❌ |
| `shared/models.py` | ❌ |
| Tests | ❌ |
| `fixtures/` | Empty |

---

## Module Structure

```
enricher/
├── pyproject.toml               # uv project config, deps, scripts
├── main.py                      # CLI entrypoint — parse mode, run pipeline
├── pipeline.py                  # PipelineOrchestrator — sequential stage runner
│
├── input/
│   ├── __init__.py
│   ├── raw_metadata_loader.py   # reads raw_metadata.json
│   ├── features_loader.py       # reads mro_features.json
│   ├── api_spec_loader.py       # parses API spec into endpoint definitions
│   └── rule_loader.py           # loads all YAML rule files
│
├── stages/
│   ├── __init__.py
│   ├── base.py                  # EnrichmentStage ABC
│   ├── stage1_name_enrichment.py
│   ├── stage2_feature_mapping.py
│   ├── stage3_relationship.py
│   ├── stage4_process_map.py
│   ├── stage5_glossary.py
│   └── stage6_usecase_gen.py
│
├── output/
│   ├── __init__.py
│   ├── enriched_assembler.py    # assembles final enriched_metadata.json
│   ├── enriched_validator.py    # validates against JSON schema
│   └── enriched_exporter.py     # format variants (future)
│
├── shared/
│   ├── __init__.py
│   ├── models.py                # Pydantic v2 models for all 11 entity types
│   ├── enrichment_context.py    # EnrichmentContext — passed through stages
│   ├── error_handler.py         # warning collection, non-fatal errors
│   └── logger.py                # structlog configuration
│
├── rules/                       # YAML — domain SMEs edit, no code changes
│   ├── name_dictionary.yaml     #   ✅ exists
│   ├── feature_rules.yaml       #   ❌
│   ├── domain_rules.yaml        #   ❌
│   ├── relationship_templates.yaml
│   ├── process_maps.yaml
│   ├── glossary.yaml
│   ├── compliance.yaml
│   ├── decision_trees.yaml
│   └── use_case_templates.yaml
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # shared fixtures
│   ├── test_pipeline.py
│   ├── test_stage1.py .. test_stage6.py
│   ├── fixtures/                # sample input data
│   └── mock_rules/              # minimal rule files for tests
│
└── fixtures/                    # real test data (empty, awaiting)
```

---

## Tech Stack & Tools

### Chosen

| Role | Library | Why |
|------|---------|-----|
| **Package manager** | [`uv`](https://docs.astral.sh/uv/) | Fast Rust-based pip/venv replacement. Single binary, lockfile, Python version mgmt. Future serverless builds stay lean. |
| **Data models** | Pydantic v2 | Type-safe dataclasses with validation, serialization, JSON Schema export. Non-negotiable for this pipeline. |
| **YAML parsing** | `PyYAML` (yaml) | Stdlib-adjacent, minimal. `ruamel.yaml` not needed — we read YAML, never write it. |
| **Logging** | `structlog` | Structured JSON logs. Processor pipeline lets us add trace_id, stage, entity context. |
| **JSON Schema** | `jsonschema` | Validate output against `docs/database/enriched_metadata_schema.json`. |
| **CLI** | `argparse` | Stdlib — zero dependencies. For serverless the entrypoint swaps to an event handler anyway. |
| **Testing** | `pytest` + `pytest-cov` | Standard. Fixtures via `conftest.py` for mock rules and sample metadata. |
| **Linter + Formatter** | [`ruff`](https://docs.astral.sh/ruff/) | Rust-based, replaces flake8/isort/black. Ships with uv, single config in `pyproject.toml`. |
| **Type checker** | `mypy` | Optional safety net. Pydantic v2 models provide runtime validation, but mypy catches logic errors in stage code. |

### Deliberately NOT chosen

| Library | Why not |
|---------|---------|
| `click` / `typer` | Another dependency for a 4-flag CLI. `argparse` is stdlib and sufficient. |
| `prefect` / `airflow` | Pipeline is sequential 6-stage, single-threaded, 38 tables. A framework is overkill. If orchestration is needed later, wrap `main.py` as a Prefect task. |
| `rich` / `click` | Pretty CLI output not needed — logs go to JSON for ELK, not terminal. |
| `orjson` / `ujson` | stdlib `json` is fast enough for 38 tables (~5 min SLA). Add only if profiling proves a bottleneck. |
| `django` / `flask` | Not an HTTP service. The enricher is a batch transform. |

### Serverless Future

Keep the core engine **dependency-light**:
- No framework lock-in — `main.py` entrypoint can be replaced with a Lambda handler
- Rule files ship alongside the deployment package
- `uv` lockfile ensures reproducible builds for Lambda layers / container images

When serverless is needed, add a thin adapter (e.g. `handler.py` with an AWS Lambda / GCP Cloud Functions entrypoint) that calls the same `pipeline.py`. No changes to stages or rules.

---

## Developer Commands

```bash
# setup
uv venv                                 # create .venv
uv sync                                 # install deps (reads pyproject.toml)

# run
uv run python main.py --mode full
uv run python main.py --mode incremental --table aircraft
uv run python main.py --mode validate

# quality
uv run ruff check .                     # lint
uv run ruff format --check .            # format check
uv run mypy src/                        # type check
uv run python -m pytest tests/ -v       # test
uv run python -m pytest tests/ --cov    # test with coverage

# build (future)
uv build                                # build wheel for deployment
```

---

## Key Design Constraints

- **Rule-based, not LLM-based** — deterministic, auditable, same input → same output
- **YAML rules, not code** — domain SMEs edit rules without deployments
- **Warnings never halt pipeline** — partial enrichment > no enrichment
- **Sequential stages** — each depends on the previous (6 stages, 38 tables)
- **Single JSON output** — `enriched_metadata.json` with 11 entity sections
- **Zero framework lock-in** — keep ready for serverless adapter
