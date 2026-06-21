"""Tests for individual enrichers."""

import pytest

from src.enrichers.name_enricher import name_to_business_name
from src.enrichers.domain_mapper import _count_domain_hits, DOMAIN_KEYWORDS
from src.enrichers.compliance_classifier import _classify_column
from src.models.metadata import ComplianceClassification


class TestNameEnricher:
    def test_simple_name(self) -> None:
        result = name_to_business_name("dob")
        assert result.business_name == "Date of birth"

    def test_snake_case(self) -> None:
        result = name_to_business_name("first_name")
        assert result.business_name == "First Name"

    def test_abbreviation(self) -> None:
        result = name_to_business_name("txn_dt")
        assert "Transaction" in result.business_name
        assert "Date" in result.business_name

    def test_id_expansion(self) -> None:
        result = name_to_business_name("cust_id")
        assert "Customer" in result.business_name
        assert "Identifier" in result.business_name

    def test_description(self) -> None:
        result = name_to_business_name("email")
        assert "email" in result.human_readable_description.lower()


class TestDomainMapper:
    def test_healthcare_detection(self) -> None:
        count = _count_domain_hits(["patients", "appointments", "doctors"], "Healthcare")
        assert count == 3

    def test_banking_detection(self) -> None:
        count = _count_domain_hits(["accounts", "transactions", "balances"], "Banking")
        assert count == 3

    def test_no_match(self) -> None:
        count = _count_domain_hits(["foo", "bar", "baz"], "Healthcare")
        assert count == 0


class TestComplianceClassifier:
    def test_email_pii(self) -> None:
        results = _classify_column("email")
        assert any(cls == ComplianceClassification.PII for cls, _ in results)

    def test_phone_pii(self) -> None:
        results = _classify_column("phone")
        assert any(cls == ComplianceClassification.PII for cls, _ in results)

    def test_ssn_pii(self) -> None:
        results = _classify_column("ssn")
        assert any(cls == ComplianceClassification.PII for cls, _ in results)

    def test_credit_card_pci(self) -> None:
        results = _classify_column("credit_card")
        assert any(cls == ComplianceClassification.PCI for cls, _ in results)

    def test_password_sensitive(self) -> None:
        results = _classify_column("password")
        assert any(cls == ComplianceClassification.SENSITIVE for cls, _ in results)

    def test_diagnosis_phi(self) -> None:
        results = _classify_column("diagnosis")
        assert any(cls == ComplianceClassification.PHI for cls, _ in results)

    def test_unknown_column(self) -> None:
        results = _classify_column("random_column_xyz")
        assert results == []
