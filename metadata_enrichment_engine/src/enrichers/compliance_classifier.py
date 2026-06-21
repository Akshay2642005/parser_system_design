"""Stage 5: Compliance Classification — identify PII, PHI, PCI, sensitive data."""

from __future__ import annotations

import logging

from src.models.metadata import (
    ClassificationEntry,
    ComplianceClassification,
    EnrichedDatabase,
    RawMetadata,
)

logger = logging.getLogger(__name__)

# Column name patterns that indicate compliance concerns
_COMPLIANCE_RULES: dict[str, list[tuple[ComplianceClassification, str]]] = {
    # PII patterns
    "email": [(ComplianceClassification.PII, "Email address is personally identifiable information")],
    "e_mail": [(ComplianceClassification.PII, "Email address is personally identifiable information")],
    "phone": [(ComplianceClassification.PII, "Phone number is personally identifiable information")],
    "mobile": [(ComplianceClassification.PII, "Mobile number is personally identifiable information")],
    "telephone": [(ComplianceClassification.PII, "Telephone number is personally identifiable information")],
    "address": [(ComplianceClassification.PII, "Physical address is personally identifiable information")],
    "street": [(ComplianceClassification.PII, "Street address is personally identifiable information")],
    "city": [(ComplianceClassification.PII, "City name may be used for identification")],
    "zip": [(ComplianceClassification.PII, "ZIP/postal code may be used for identification")],
    "postal_code": [(ComplianceClassification.PII, "Postal code may be used for identification")],
    "ssn": [(ComplianceClassification.PII, "Social Security Number is sensitive PII")],
    "social_security": [(ComplianceClassification.PII, "Social Security Number is sensitive PII")],
    "aadhaar": [(ComplianceClassification.PII, "Aadhaar number is sensitive PII (India)")],
    "pan": [(ComplianceClassification.PII, "PAN number is sensitive PII (India)")],
    "passport": [(ComplianceClassification.PII, "Passport number is sensitive PII")],
    "passport_no": [(ComplianceClassification.PII, "Passport number is sensitive PII")],
    "driver_license": [(ComplianceClassification.PII, "Driver license number is sensitive PII")],
    "license_no": [(ComplianceClassification.PII, "License number is sensitive PII")],
    "date_of_birth": [(ComplianceClassification.PII, "Date of birth is personally identifiable information")],
    "dob": [(ComplianceClassification.PII, "Date of birth is personally identifiable information")],
    "birth_date": [(ComplianceClassification.PII, "Date of birth is personally identifiable information")],
    "full_name": [(ComplianceClassification.PII, "Full name is personally identifiable information")],
    "first_name": [(ComplianceClassification.PII, "First name is personally identifiable information")],
    "last_name": [(ComplianceClassification.PII, "Last name is personally identifiable information")],
    "username": [(ComplianceClassification.PII, "Username may be used for identification")],
    "ip_address": [(ComplianceClassification.PII, "IP address is personally identifiable information")],
    "nationality": [(ComplianceClassification.PII, "Nationality is personally identifiable information")],
    "gender": [(ComplianceClassification.PII, "Gender is personally identifiable information")],
    "marital_status": [(ComplianceClassification.PII, "Marital status is sensitive PII")],

    # PHI patterns (Healthcare)
    "diagnosis": [(ComplianceClassification.PHI, "Diagnosis is protected health information")],
    "treatment": [(ComplianceClassification.PHI, "Treatment information is PHI")],
    "medication": [(ComplianceClassification.PHI, "Medication data is protected health information")],
    "prescription": [(ComplianceClassification.PHI, "Prescription data is protected health information")],
    "medical_record": [(ComplianceClassification.PHI, "Medical record number is PHI")],
    "patient_id": [(ComplianceClassification.PHI, "Patient identifier is PHI in healthcare context")],
    "health_plan": [(ComplianceClassification.PHI, "Health plan information is PHI")],
    "lab_result": [(ComplianceClassification.PHI, "Lab results are protected health information")],
    "vital_sign": [(ComplianceClassification.PHI, "Vital signs are protected health information")],
    "allergy": [(ComplianceClassification.PHI, "Allergy information is PHI")],

    # PCI patterns
    "credit_card": [(ComplianceClassification.PCI, "Credit card number is PCI-regulated data")],
    "card_number": [(ComplianceClassification.PCI, "Card number is PCI-regulated data")],
    "card_no": [(ComplianceClassification.PCI, "Card number is PCI-regulated data")],
    "cvv": [(ComplianceClassification.PCI, "CVV is PCI-regulated data")],
    "exp_date": [(ComplianceClassification.PCI, "Expiration date is PCI-regulated data")],
    "expiry": [(ComplianceClassification.PCI, "Expiry date is PCI-regulated data")],
    "bank_account": [(ComplianceClassification.PCI, "Bank account number is PCI-regulated data")],
    "routing_number": [(ComplianceClassification.PCI, "Routing number is financial data")],
    "ifsc": [(ComplianceClassification.PCI, "IFSC code is financial data")],
    "swift": [(ComplianceClassification.PCI, "SWIFT code is financial data")],
    "iban": [(ComplianceClassification.PCI, "IBAN is PCI-regulated data")],

    # Financial patterns
    "salary": [(ComplianceClassification.FINANCIAL, "Salary is financial compensation data")],
    "compensation": [(ComplianceClassification.FINANCIAL, "Compensation data is financial information")],
    "income": [(ComplianceClassification.FINANCIAL, "Income data is financial information")],
    "balance": [(ComplianceClassification.FINANCIAL, "Account balance is financial information")],
    "transaction_amount": [(ComplianceClassification.FINANCIAL, "Transaction amount is financial data")],

    # Sensitive patterns
    "password": [(ComplianceClassification.SENSITIVE, "Password is sensitive authentication data")],
    "passwd": [(ComplianceClassification.SENSITIVE, "Password is sensitive authentication data")],
    "secret": [(ComplianceClassification.SENSITIVE, "Secret data is sensitive")],
    "token": [(ComplianceClassification.SENSITIVE, "Authentication token is sensitive data")],
    "api_key": [(ComplianceClassification.SENSITIVE, "API key is sensitive data")],
    "private_key": [(ComplianceClassification.SENSITIVE, "Private key is sensitive data")],
}


def _classify_column(col_name: str) -> list[tuple[ComplianceClassification, str]]:
    """Return list of (classification, reason) for a column name."""
    name_lower = col_name.lower().strip()

    # Exact match first
    if name_lower in _COMPLIANCE_RULES:
        return _COMPLIANCE_RULES[name_lower]

    # Substring match
    results: list[tuple[ComplianceClassification, str]] = []
    for pattern, rules in _COMPLIANCE_RULES.items():
        if pattern in name_lower or name_lower in pattern:
            results.extend(rules)

    return results


def enrich(metadata: RawMetadata, enriched: EnrichedDatabase) -> None:
    """Stage 5: classify columns for compliance concerns."""
    for table in metadata.tables:
        for col in table.columns:
            classifications = _classify_column(col.name)
            for cls, reason in classifications:
                enriched.classifications.append(
                    ClassificationEntry(
                        column=col.name,
                        table=table.name,
                        classification=cls,
                        reason=reason,
                    )
                )

    logger.info(
        "Compliance classification: %d classified column(s)",
        len(enriched.classifications),
    )
