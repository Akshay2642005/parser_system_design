"""CLI entry point for the Metadata Enrichment Engine."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from src.pipeline.enrichment_pipeline import enrich_metadata


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="meta-enrich",
        description="Metadata Enrichment Engine — convert database metadata into AI-ready JSON.",
    )
    parser.add_argument(
        "metadata",
        help="Path to metadata TXT file or directory containing TXT files",
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path to write enriched JSON output (default: stdout)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: true)",
    )

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    metadata_path = Path(args.metadata)
    if not metadata_path.exists():
        print(f"Error: path '{metadata_path}' does not exist", file=sys.stderr)
        return 1

    try:
        result = enrich_metadata(
            metadata_txt_path=str(metadata_path),
            config_path=args.config,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        logging.getLogger(__name__).exception("Enrichment failed")
        return 1

    if not args.output:
        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
