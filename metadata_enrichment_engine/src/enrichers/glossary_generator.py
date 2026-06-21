"""Stage 4: Glossary Generation — generate business glossary entries."""

from __future__ import annotations

import logging

from src.models.metadata import EnrichedDatabase, GlossaryEntry, RawMetadata

logger = logging.getLogger(__name__)

# Table-name -> glossary definition templates
_TABLE_GLOSSARY: dict[str, str] = {
    "patients": "Individual receiving healthcare services",
    "appointments": "Scheduled visit between a patient and provider",
    "doctors": "Licensed medical professional providing care",
    "prescriptions": "Medication order issued by a physician",
    "diagnosis": "Identification of a patient condition",
    "orders": "Customer purchase request for products or services",
    "customers": "Individual or entity that purchases products or services",
    "products": "Goods or services offered for sale",
    "inventory": "Stock of products available for sale or distribution",
    "employees": "Individuals working for the organization",
    "departments": "Organizational units within the company",
    "transactions": "Financial exchange records",
    "accounts": "Financial accounts holding balances",
    "payments": "Records of financial transfers",
    "invoices": "Billing documents for goods or services",
    "shipments": "Records of product delivery",
    "suppliers": "Entities providing goods or services to the organization",
    "vendors": "External organizations supplying products or services",
    "users": "Individuals with system access",
    "roles": "Permission groups assigned to users",
    "permissions": "Access rights granted to roles or users",
    "logs": "System-generated records of events or actions",
    "sessions": "Active user interaction periods with the system",
    "policies": "Insurance or compliance policy definitions",
    "claims": "Requests for insurance coverage or reimbursement",
    "benefits": "Employee benefits or insurance coverage details",
    "salary": "Employee compensation records",
    "payroll": "Processed employee payment records",
    "attendance": "Employee presence and absence records",
    "courses": "Educational course definitions",
    "students": "Individuals enrolled in educational programs",
    "enrollments": "Student registrations for courses",
    "grades": "Academic performance records",
    "shipments": "Product delivery tracking records",
    "routes": "Delivery or transportation paths",
    "warehouses": "Storage facilities for inventory",
    "products": "Goods available for sale or distribution",
}

# Column-name -> glossary definition templates
_COLUMN_GLOSSARY: dict[str, str] = {
    "id": "Unique identifier for the record",
    "name": "Name or label of the entity",
    "email": "Email address for electronic communication",
    "phone": "Telephone contact number",
    "address": "Physical mailing address",
    "dob": "Date of birth of the individual",
    "ssn": "Social Security Number",
    "created_at": "Timestamp when the record was created",
    "updated_at": "Timestamp when the record was last modified",
    "status": "Current state or status of the record",
    "description": "Textual description or notes",
    "amount": "Monetary value associated with the record",
    "price": "Unit price for a product or service",
    "quantity": "Number of units",
    "total": "Calculated total value",
    "date": "Date associated with the record",
    "start_date": "Beginning date of the event or period",
    "end_date": "Ending date of the event or period",
    "is_active": "Flag indicating if the record is active",
    "is_deleted": "Soft-delete flag",
    "type": "Category or classification of the record",
    "category": "Classification group for the record",
    "priority": "Priority level of the record",
    "rating": "Quality or satisfaction rating",
    "discount": "Reduction applied to price or amount",
    "tax": "Tax applied to the transaction",
    "total_amount": "Final amount including tax and discounts",
    "currency": "Currency code for monetary values",
    "created_by": "User or system that created the record",
    "updated_by": "User or system that last modified the record",
    "version": "Version number for optimistic locking",
}


def _singularize(table_name: str) -> str:
    """Basic singularization of a table name."""
    name = table_name.rstrip("s")
    if name.endswith("ie"):
        name = name[:-2] + "y"
    elif name.endswith("ses"):
        name = name[:-2]
    elif name.endswith("xes"):
        name = name[:-2]
    return name


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 4: generate glossary entries."""
    seen: set[str] = set()

    for table in metadata.tables:
        # Table-level glossary
        key = table.name.lower()
        definition = _TABLE_GLOSSARY.get(key)
        if not definition:
            singular = _singularize(table.name)
            definition = f"Collection of {singular} records"
        term = table.name.replace("_", " ").title()
        if term not in seen:
            enriched.business_glossary.append(
                GlossaryEntry(term=term, definition=definition)
            )
            seen.add(term)

        # Column-level glossary
        for col in table.columns:
            col_key = col.name.lower()
            col_def = _COLUMN_GLOSSARY.get(col_key)
            if not col_def:
                col_def = f"Attribute of the {table.name.rstrip('s')} entity"
            col_term = col.name.replace("_", " ").title()
            if col_term not in seen:
                enriched.business_glossary.append(
                    GlossaryEntry(term=col_term, definition=col_def)
                )
                seen.add(col_term)

    logger.info("Glossary generation: %d entries", len(enriched.business_glossary))
