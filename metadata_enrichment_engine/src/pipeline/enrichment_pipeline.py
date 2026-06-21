"""Enrichment pipeline — orchestrates all enrichment stages."""

from __future__ import annotations

import logging
from pathlib import Path

from src.enrichers import (
    alert_generator,
    compliance_classifier,
    domain_mapper,
    glossary_generator,
    name_enricher,
    process_discovery,
    relationship_discovery,
    usecase_generator,
)
from src.models.metadata import EnrichedDatabase, EnrichedOutput, RawMetadata
from src.parser.config_loader import AppConfig, load_config
from src.parser.txt_parser import parse_metadata_txt

logger = logging.getLogger(__name__)

# Ordered list of enrichment stages
STAGES: list[tuple[str, any]] = [
    ("name_enrichment", name_enricher.enrich),
    ("domain_mapping", domain_mapper.enrich),
    ("relationship_discovery", relationship_discovery.enrich),
    ("glossary_generation", glossary_generator.enrich),
    ("compliance_classification", compliance_classifier.enrich),
    ("usecase_generation", usecase_generator.enrich),
    ("process_discovery", process_discovery.enrich),
    ("alert_generation", alert_generator.enrich),
]


def enrich_single_database(
    metadata: RawMetadata,
    stages: list[tuple[str, any]] | None = None,
) -> EnrichedDatabase:
    """Run all enrichment stages on a single RawMetadata object."""
    enriched = EnrichedDatabase(
        database_info=metadata.database,
        tables=metadata.tables,
        relationships=[
            rel
            for table in metadata.tables
            for rel in table.relationships
        ],
    )

    active_stages = stages or STAGES
    for stage_name, stage_fn in active_stages:
        logger.info("Running stage: %s", stage_name)
        try:
            stage_fn(metadata, enriched)
        except Exception:
            logger.exception("Stage '%s' failed", stage_name)
            raise

    logger.info(
        "Enrichment complete for '%s': %d alerts, %d glossary, %d classifications",
        metadata.database.name,
        len(enriched.alerts),
        len(enriched.business_glossary),
        len(enriched.classifications),
    )
    return enriched


def enrich_metadata(
    metadata_txt_path: str | Path,
    config_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict:
    """High-level API: parse inputs, run enrichment, return JSON dict.

    Parameters
    ----------
    metadata_txt_path:
        Path to the metadata TXT file(s). Can be a single file or a directory.
    config_path:
        Optional path to the YAML config file.
    output_path:
        Optional path to write the enriched JSON output.

    Returns
    -------
    dict
        The enriched metadata as a JSON-serializable dictionary.
    """
    from src.output.json_serializer import to_json_dict

    # Load config
    config: AppConfig = AppConfig()
    if config_path:
        config = load_config(config_path)

    # Discover TXT files
    txt_path = Path(metadata_txt_path)
    if txt_path.is_dir():
        txt_files = sorted(txt_path.glob("*.txt"))
    else:
        txt_files = [txt_path]

    if not txt_files:
        logger.warning("No metadata TXT files found at %s", metadata_txt_path)
        return to_json_dict(EnrichedOutput())

    # Build a config lookup
    config_lookup: dict[str, any] = {
        db.id: db for db in config.databases
    }

    output = EnrichedOutput()

    for txt_file in txt_files:
        # Try to match config by filename stem
        db_config = config_lookup.get(txt_file.stem)
        from src.parser.config_loader import config_to_database_info

        db_info = config_to_database_info(db_config) if db_config else None

        logger.info("Processing %s", txt_file)
        raw = parse_metadata_txt(txt_file, db_info)
        enriched = enrich_single_database(raw)
        output.databases.append(enriched)

    # Write output
    result = to_json_dict(output)

    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        logger.info("Output written to %s", out_path)

    return result
