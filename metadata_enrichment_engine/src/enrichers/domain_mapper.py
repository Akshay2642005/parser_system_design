"""Stage 2: Domain Mapping — infer business domain from table/column names."""

from __future__ import annotations

import logging

from src.models.metadata import DomainScore, EnrichedDatabase, RawMetadata

logger = logging.getLogger(__name__)

# Domain keyword mappings (order = priority)
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "Healthcare": [
        "patient", "appointment", "diagnosis", "prescription", "doctor",
        "physician", "medical", "health", "clinic", "hospital", "treatment",
        "symptom", "medication", "dosage", "insurance", "claim", "pharmacy",
        "lab", "radiology", "nurse", "ward", "bed", "surgery", "procedure",
    ],
    "Banking": [
        "account", "transaction", "balance", "deposit", "withdrawal",
        "transfer", "loan", "credit", "debit", "interest", "rate",
        "currency", "exchange", "portfolio", "investment", "stock",
        "bond", "mutual", "fund", "dividend", "broker", "trading",
    ],
    "Retail": [
        "order", "customer", "product", "cart", "checkout", "invoice",
        "shipping", "inventory", "warehouse", "supplier", "vendor",
        "discount", "coupon", "promotion", "catalog", "category",
        "payment", "refund", "return", "purchase", "sale", "price",
    ],
    "E-Commerce": [
        "order", "customer", "product", "cart", "checkout", "invoice",
        "shipping", "inventory", "warehouse", "supplier", "vendor",
        "discount", "coupon", "promotion", "catalog", "category",
        "payment", "refund", "return", "purchase", "sale", "price",
        "review", "rating", "wishlist", "session", "cart",
    ],
    "HR": [
        "employee", "department", "salary", "payroll", "benefit",
        "leave", "attendance", "performance", "review", "recruitment",
        "candidate", "interview", "offer", "onboarding", "training",
        "role", "position", "manager", "report", "headcount",
    ],
    "Education": [
        "student", "course", "enrollment", "grade", "gpa",
        "semester", "faculty", "department", "class", "exam",
        "assignment", "attendance", "scholarship", "tuition",
    ],
    "Manufacturing": [
        "product", "assembly", "component", "raw_material", "bill_of_material",
        "work_order", "production", "quality", "inspection", "defect",
        "yield", "batch", "lot", "machine", "downtime",
    ],
    "Logistics": [
        "shipment", "tracking", "route", "warehouse", "carrier",
        "freight", "delivery", "dispatch", "manifest", "consignment",
        "pickup", "dropoff", "fleet", "vehicle", "driver",
    ],
    "Insurance": [
        "policy", "premium", "claim", "coverage", "deductible",
        "underwriting", "risk", "adjuster", "beneficiary", "insured",
    ],
    "Telecom": [
        "subscriber", "plan", "call", "sms", "data", "roaming",
        "tower", "signal", "bandwidth", "latency", "band",
    ],
}


def _count_domain_hits(table_names: list[str], domain: str) -> int:
    keywords = DOMAIN_KEYWORDS.get(domain, [])
    count = 0
    for tname in table_names:
        tname_lower = tname.lower()
        for kw in keywords:
            if kw in tname_lower:
                count += 1
                break
    return count


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 2: infer business domains."""
    table_names = [t.name for t in metadata.tables]
    total = len(table_names) if table_names else 1

    scores: list[DomainScore] = []
    for domain in DOMAIN_KEYWORDS:
        hits = _count_domain_hits(table_names, domain)
        if hits > 0:
            confidence = round(min(hits / total, 1.0), 2)
            scores.append(DomainScore(domain=domain, confidence=confidence))

    scores.sort(key=lambda d: d.confidence, reverse=True)
    enriched.domains = scores[:5]  # Top 5

    logger.info(
        "Domain mapping: %d domain(s) detected, top=%s",
        len(enriched.domains),
        enriched.domains[0].domain if enriched.domains else "none",
    )
