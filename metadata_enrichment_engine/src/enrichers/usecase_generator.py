"""Stage 6: Use Case Generation — infer likely use cases from schema."""

from __future__ import annotations

import logging

from src.models.metadata import EnrichedDatabase, RawMetadata, UseCase

logger = logging.getLogger(__name__)

# Domain-specific use case templates
_DOMAIN_USECASES: dict[str, list[UseCase]] = {
    "Healthcare": [
        UseCase(name="Patient Search", description="Search patients by name, phone, or email"),
        UseCase(name="Appointment Scheduling", description="Book and manage patient appointments"),
        UseCase(name="Prescription Management", description="Create and track prescriptions"),
        UseCase(name="Diagnosis Lookup", description="Retrieve patient diagnosis history"),
        UseCase(name="Patient Record Export", description="Export patient records for transfer"),
    ],
    "Banking": [
        UseCase(name="Account Balance Inquiry", description="Check account balances"),
        UseCase(name="Transaction History", description="View transaction history for accounts"),
        UseCase(name="Fund Transfer", description="Transfer funds between accounts"),
        UseCase(name="Loan Application Processing", description="Process loan applications"),
    ],
    "Retail": [
        UseCase(name="Product Catalog Browsing", description="Browse products by category"),
        UseCase(name="Order Processing", description="Process customer orders end-to-end"),
        UseCase(name="Inventory Management", description="Track and manage product inventory"),
        UseCase(name="Customer Order History", description="View past orders for a customer"),
        UseCase(name="Invoice Generation", description="Generate invoices for completed orders"),
    ],
    "HR": [
        UseCase(name="Employee Directory", description="Search and browse employee records"),
        UseCase(name="Payroll Processing", description="Generate and process payroll"),
        UseCase(name="Leave Management", description="Apply for and manage employee leave"),
        UseCase(name="Performance Review", description="Track employee performance reviews"),
    ],
}

# Table-name based use case generation
_TABLE_USECASES: dict[str, list[UseCase]] = {
    "patients": [
        UseCase(name="Patient Registration", description="Register new patients"),
        UseCase(name="Patient Search", description="Search patients by various criteria"),
    ],
    "appointments": [
        UseCase(name="Appointment Booking", description="Schedule new appointments"),
        UseCase(name="Appointment Calendar", description="View upcoming appointments"),
    ],
    "orders": [
        UseCase(name="Order Placement", description="Place new orders"),
        UseCase(name="Order Tracking", description="Track order status"),
    ],
    "customers": [
        UseCase(name="Customer Registration", description="Register new customers"),
        UseCase(name="Customer Lookup", description="Search for customer records"),
    ],
    "products": [
        UseCase(name="Product Search", description="Search product catalog"),
        UseCase(name="Product Management", description="Add, edit, remove products"),
    ],
    "employees": [
        UseCase(name="Employee Onboarding", description="Add new employees to the system"),
    ],
    "transactions": [
        UseCase(name="Transaction Processing", description="Process financial transactions"),
        UseCase(name="Transaction Reporting", description="Generate transaction reports"),
    ],
    "accounts": [
        UseCase(name="Account Management", description="Create and manage accounts"),
    ],
    "payments": [
        UseCase(name="Payment Processing", description="Process incoming and outgoing payments"),
    ],
    "invoices": [
        UseCase(name="Invoice Generation", description="Generate invoices for services"),
        UseCase(name="Payment Collection", description="Track and collect invoice payments"),
    ],
    "inventory": [
        UseCase(name="Stock Management", description="Track inventory levels"),
    ],
    "shipments": [
        UseCase(name="Shipment Tracking", description="Track delivery shipments"),
    ],
    "users": [
        UseCase(name="User Management", description="Manage user accounts and access"),
    ],
    "logs": [
        UseCase(name="Audit Trail", description="Review system activity logs"),
    ],
}


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 6: generate use cases based on schema."""
    seen: set[str] = set()

    # Domain-based use cases
    for domain in enriched.domains:
        domain_cases = _DOMAIN_USECASES.get(domain.domain, [])
        for uc in domain_cases:
            if uc.name not in seen:
                enriched.use_cases.append(uc)
                seen.add(uc.name)

    # Table-based use cases
    for table in metadata.tables:
        table_key = table.name.lower().rstrip("s")
        for key, cases in _TABLE_USECASES.items():
            if key in table_key or table_key in key:
                for uc in cases:
                    if uc.name not in seen:
                        enriched.use_cases.append(uc)
                        seen.add(uc.name)

    # Generic use cases based on column patterns
    for table in metadata.tables:
        has_search_cols = any(
            c.name.lower() in ("name", "email", "phone", "search_term", "query")
            for c in table.columns
        )
        if has_search_cols:
            uc = UseCase(
                name=f"{table.name.title()} Search",
                description=f"Search {table.name} records using name, email, or phone",
            )
            if uc.name not in seen:
                enriched.use_cases.append(uc)
                seen.add(uc.name)

        has_status = any(c.name.lower() == "status" for c in table.columns)
        if has_status:
            uc = UseCase(
                name=f"{table.name.title()} Status Tracking",
                description=f"Track status changes for {table.name}",
            )
            if uc.name not in seen:
                enriched.use_cases.append(uc)
                seen.add(uc.name)

        has_timestamps = any(
            c.name.lower() in ("created_at", "updated_at", "timestamp")
            for c in table.columns
        )
        if has_timestamps and len(table.columns) > 3:
            uc = UseCase(
                name=f"{table.name.title()} Audit Trail",
                description=f"Track creation and modification of {table.name} records",
            )
            if uc.name not in seen:
                enriched.use_cases.append(uc)
                seen.add(uc.name)

    logger.info("Use case generation: %d use case(s)", len(enriched.use_cases))
