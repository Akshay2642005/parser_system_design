"""Stage 1: Name Enrichment — convert technical names to business-friendly names."""

from __future__ import annotations

import logging
import re

from src.models.metadata import BusinessName, EnrichedDatabase, RawMetadata

logger = logging.getLogger(__name__)

# Common abbreviation expansions
_ABBREVIATIONS: dict[str, str] = {
    "id": "Identifier",
    "pk": "Primary Key",
    "fk": "Foreign Key",
    "dt": "Date",
    "amt": "Amount",
    "qty": "Quantity",
    "desc": "Description",
    "num": "Number",
    "nm": "Name",
    "addr": "Address",
    "dob": "Date Of Birth",
    "ssn": "Social Security Number",
    "cc": "Credit Card",
    "txn": "Transaction",
    "mgr": "Manager",
    "emp": "Employee",
    "cust": "Customer",
    "prod": "Product",
    "cat": "Category",
    "loc": "Location",
    "tel": "Telephone",
    "msg": "Message",
    "img": "Image",
    "ref": "Reference",
    "upd": "Update",
    "ins": "Insert",
    "del": "Delete",
    "ts": "Timestamp",
    "tsz": "Timestamp With Timezone",
    "meta": "Metadata",
    "tmp": "Temporary",
    "cnt": "Count",
    "stat": "Status",
    "cd": "Code",
    "grp": "Group",
    "auth": "Authentication",
    "perm": "Permission",
    "priv": "Privilege",
    "dept": "Department",
    "sal": "Salary",
    "qty": "Quantity",
    "inv": "Inventory",
    "po": "Purchase Order",
    "sku": "Stock Keeping Unit",
    "url": "URL",
    "btn": "Button",
    "img": "Image",
    "usr": "User",
    "pwd": "Password",
    "auth": "Authentication",
    "sess": "Session",
    "cfg": "Configuration",
    "log": "Log",
    "err": "Error",
    "req": "Request",
    "res": "Response",
    "fmt": "Format",
    "tmp": "Template",
    "doc": "Document",
    "docx": "Document",
    "img": "Image",
    "txn": "Transaction",
    "bal": "Balance",
    "cr": "Credit",
    "dr": "Debit",
    "curr": "Currency",
    "fx": "Exchange Rate",
    "apr": "Annual Percentage Rate",
    "roi": "Return On Investment",
    "ytd": "Year To Date",
    "mtd": "Month To Date",
    "qtd": "Quarter To Date",
    "yr": "Year",
    "mo": "Month",
    "wk": "Week",
    "hr": "Hour",
    "min": "Minute",
    "sec": "Second",
    "ms": "Millisecond",
    "us": "Microsecond",
    "ns": "Nanosecond",
    "lat": "Latitude",
    "lon": "Longitude",
    "lng": "Longitude",
    "alt": "Altitude",
    "elev": "Elevation",
    "dist": "Distance",
    "sp": "Speed",
    "vel": "Velocity",
    "acc": "Acceleration",
    "temp": "Temperature",
    "hum": "Humidity",
    "pres": "Pressure",
    "vis": "Visibility",
    "wind": "Wind",
    "precip": "Precipitation",
    "uv": "UV Index",
    "aqi": "Air Quality Index",
}

# Snake-case and camelCase word splitting
_WORD_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$|\d)|\d+")


def _split_name(name: str) -> list[str]:
    """Split a snake_case, camelCase, or mixed name into words."""
    name = name.lower().replace("-", "_")
    words = _WORD_RE.findall(name)
    return [w for w in words if w]


def _expand_abbreviation(word: str) -> str:
    return _ABBREVIATIONS.get(word.lower(), word)


def _capitalize_words(words: list[str]) -> str:
    return " ".join(w.capitalize() for w in words)


def name_to_business_name(raw_name: str) -> BusinessName:
    """Convert a technical column/table name to a business name."""
    words = _split_name(raw_name)
    expanded = [_expand_abbreviation(w) for w in words]
    business = _capitalize_words(expanded)

    if not business:
        business = raw_name

    description = f"The {business.lower()} field"
    return BusinessName(
        technical_name=raw_name,
        business_name=business,
        human_readable_description=description,
    )


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 1: populate business_names on enriched output."""
    seen: set[str] = set()

    for table in metadata.tables:
        entry = name_to_business_name(table.name)
        if entry.technical_name not in seen:
            enriched.business_names.append(entry)
            seen.add(entry.technical_name)

        for col in table.columns:
            entry = name_to_business_name(col.name)
            if entry.technical_name not in seen:
                enriched.business_names.append(entry)
                seen.add(entry.technical_name)

    logger.info("Name enrichment: %d names generated", len(enriched.business_names))
