"""Stage 7: Process Discovery — infer business workflows from table groupings."""

from __future__ import annotations

import logging

from src.models.metadata import BusinessProcess, EnrichedDatabase, RawMetadata

logger = logging.getLogger(__name__)

# Table-grouping patterns that imply business processes
_PROCESS_PATTERNS: list[tuple[str, list[str], str, str]] = [
    (
        "Patient Care Lifecycle",
        ["patients", "appointments", "doctors", "prescriptions", "diagnosis", "treatment"],
        "End-to-end patient care from registration through treatment",
        "healthcare",
    ),
    (
        "Order Fulfillment",
        ["customers", "orders", "order_items", "products", "shipments", "payments", "invoices"],
        "Customer order processing from placement to delivery",
        "retail",
    ),
    (
        "Employee Management",
        ["employees", "departments", "salary", "payroll", "benefits", "attendance", "leave"],
        "Employee lifecycle from hiring through compensation",
        "hr",
    ),
    (
        "Financial Transaction Processing",
        ["accounts", "transactions", "balances", "payments", "transfers"],
        "End-to-end financial transaction lifecycle",
        "banking",
    ),
    (
        "Inventory Management",
        ["products", "inventory", "warehouses", "suppliers", "purchase_orders"],
        "Stock management from procurement to warehouse storage",
        "manufacturing",
    ),
    (
        "User Access Management",
        ["users", "roles", "permissions", "sessions", "audit_logs"],
        "User authentication, authorization, and session tracking",
        "security",
    ),
    (
        "Claims Processing",
        ["claims", "policies", "customers", "adjusters", "payments"],
        "Insurance claim lifecycle from filing to settlement",
        "insurance",
    ),
    (
        "Student Enrollment",
        ["students", "courses", "enrollments", "grades", "faculty"],
        "Academic enrollment and grading process",
        "education",
    ),
    (
        "Shipment Tracking",
        ["shipments", "routes", "carriers", "warehouses", "deliveries"],
        "Logistics from dispatch to delivery",
        "logistics",
    ),
]


def _score_tables(table_names: list[str], pattern_tables: list[str]) -> float:
    """Score how well the schema matches a process pattern."""
    lower_names = {t.lower().rstrip("s") for t in table_names}
    lower_pattern = {p.lower().rstrip("s") for p in pattern_tables}
    matches = lower_names & lower_pattern
    if not lower_pattern:
        return 0.0
    return round(len(matches) / len(lower_pattern), 2)


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 7: discover business processes."""
    table_names = [t.name for t in metadata.tables]

    for process_name, pattern_tables, description, _category in _PROCESS_PATTERNS:
        score = _score_tables(table_names, pattern_tables)
        if score >= 0.3:  # At least 30% overlap
            involved = [
                t for t in table_names
                if t.lower().rstrip("s") in {p.lower().rstrip("s") for p in pattern_tables}
            ]
            enriched.business_processes.append(
                BusinessProcess(
                    process=process_name,
                    description=description,
                    tables_involved=involved,
                )
            )

    logger.info(
        "Process discovery: %d business process(es)", len(enriched.business_processes)
    )
