"""
Unit tests for Master Data Service

Tests for:
- normalize_tax_code: Remove spaces, dashes, uppercase
- normalize_company_name: Lowercase, remove accents, remove special chars
- calculate_similarity: Levenshtein distance similarity ratio
- match_importer: Tax code and fuzzy name matching
- match_exporter: Exact and fuzzy name matching
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.models.exporter import Exporter
from src.models.importer import Importer
from src.services.master_data_service import (
    calculate_similarity,
    match_exporter,
    match_importer,
    normalize_company_name,
    normalize_tax_code,
)

# ========================================
# Test normalize_tax_code
# ========================================

def test_normalize_tax_code_removes_spaces():
    """Test that normalize_tax_code removes spaces."""
    assert normalize_tax_code("0123 456 789") == "0123456789"


def test_normalize_tax_code_removes_dashes():
    """Test that normalize_tax_code removes dashes."""
    assert normalize_tax_code("0123-456-789") == "0123456789"


def test_normalize_tax_code_removes_mixed_separators():
    """Test that normalize_tax_code removes multiple types of separators."""
    assert normalize_tax_code("0123-456 789.012") == "0123456789012"


def test_normalize_tax_code_converts_to_uppercase():
    """Test that normalize_tax_code converts letters to uppercase."""
    assert normalize_tax_code("abc123xyz") == "ABC123XYZ"
    assert normalize_tax_code("test-code-123") == "TESTCODE123"


def test_normalize_tax_code_handles_empty_string():
    """Test that normalize_tax_code handles empty string."""
    assert normalize_tax_code("") == ""


def test_normalize_tax_code_handles_none():
    """Test that normalize_tax_code handles None."""
    assert normalize_tax_code(None) == ""


def test_normalize_tax_code_removes_special_chars():
    """Test that normalize_tax_code removes special characters."""
    assert normalize_tax_code("0123@456#789") == "0123456789"
    assert normalize_tax_code("ABC!@#$123") == "ABC123"


# ========================================
# Test normalize_company_name
# ========================================

def test_normalize_company_name_converts_to_lowercase():
    """Test that normalize_company_name converts to lowercase."""
    assert normalize_company_name("ABC COMPANY") == "abc company"


def test_normalize_company_name_removes_vietnamese_accents():
    """Test that normalize_company_name removes Vietnamese accents."""
    assert normalize_company_name("Công ty TNHH ABC") == "cong ty tnhh abc"
    assert normalize_company_name("Hà Nội") == "ha noi"


def test_normalize_company_name_removes_special_chars():
    """Test that normalize_company_name removes special characters."""
    assert normalize_company_name("Company (USA)") == "company usa"
    assert normalize_company_name("ABC & Co., Ltd.") == "abc co ltd"
    assert normalize_company_name("Test@#$Company!") == "testcompany"


def test_normalize_company_name_collapses_spaces():
    """Test that normalize_company_name collapses multiple spaces."""
    assert normalize_company_name("Company   Name   Here") == "company name here"
    assert normalize_company_name("  Multiple  Spaces  ") == "multiple spaces"


def test_normalize_company_name_trims_whitespace():
    """Test that normalize_company_name trims leading/trailing whitespace."""
    assert normalize_company_name("  Company Name  ") == "company name"


def test_normalize_company_name_handles_empty_string():
    """Test that normalize_company_name handles empty string."""
    assert normalize_company_name("") == ""


def test_normalize_company_name_handles_none():
    """Test that normalize_company_name handles None."""
    assert normalize_company_name(None) == ""


def test_normalize_company_name_complex_vietnamese():
    """Test normalize_company_name with complex Vietnamese text."""
    # Vietnamese: "Công ty TNHH XYZ (Việt Nam)"
    # Expected: "cong ty tnhh xyz viet nam"
    result = normalize_company_name("Công ty TNHH XYZ (Việt Nam)")
    assert result == "cong ty tnhh xyz viet nam"


def test_normalize_company_name_keeps_numbers():
    """Test that normalize_company_name preserves numbers."""
    assert normalize_company_name("Company 123") == "company 123"


# ========================================
# Test calculate_similarity
# ========================================

def test_calculate_similarity_identical_strings():
    """Test that calculate_similarity returns 1.0 for identical strings."""
    assert calculate_similarity("hello", "hello") == 1.0
    assert calculate_similarity("Company ABC", "Company ABC") == 1.0


def test_calculate_similarity_completely_different():
    """Test calculate_similarity with completely different strings."""
    result = calculate_similarity("hello", "world")
    assert 0.0 <= result < 0.5  # Should be low similarity


def test_calculate_similarity_partial_match():
    """Test calculate_similarity with partial matches."""
    result = calculate_similarity("company abc", "company xyz")
    assert 0.5 <= result < 1.0  # Should be moderate similarity (same prefix)


def test_calculate_similarity_case_sensitive():
    """Test that calculate_similarity is case-sensitive."""
    # Note: similarity is case-sensitive, so normalization should be done before
    result1 = calculate_similarity("HELLO", "hello")
    result2 = calculate_similarity("hello", "hello")
    assert result1 < result2
    assert result2 == 1.0


def test_calculate_similarity_empty_strings():
    """Test calculate_similarity with empty strings."""
    assert calculate_similarity("", "") == 0.0
    assert calculate_similarity("hello", "") == 0.0
    assert calculate_similarity("", "world") == 0.0


def test_calculate_similarity_none_values():
    """Test calculate_similarity with None values."""
    assert calculate_similarity(None, None) == 0.0
    assert calculate_similarity("hello", None) == 0.0
    assert calculate_similarity(None, "world") == 0.0


def test_calculate_similarity_high_threshold():
    """Test calculate_similarity with strings above 85% similarity."""
    # Very similar strings (one character different)
    result = calculate_similarity("company abc ltd", "company abc ltc")
    assert result >= 0.85


def test_calculate_similarity_below_threshold():
    """Test calculate_similarity with strings below 85% similarity."""
    result = calculate_similarity("company abc", "totally different name")
    assert result < 0.85


# ========================================
# Test match_importer (async)
# ========================================

@pytest.mark.asyncio
async def test_match_importer_exact_tax_code_match(db_session, test_organization):
    """Test that match_importer finds exact tax_code match."""
    # Create importer with normalized tax code
    importer = Importer(
        id=uuid4(),
        tax_code="0123456789",  # Already normalized
        name="Test Company",
        name_normalized="test company",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(importer)
    await db_session.commit()

    # Test with un-normalized tax code
    result = await match_importer(
        extracted_tax_code="0123-456-789",  # Will be normalized to match
        extracted_name=None,
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is not None
    assert result.id == importer.id
    assert result.tax_code == "0123456789"


@pytest.mark.asyncio
async def test_match_importer_fuzzy_name_match_above_threshold(db_session, test_organization):
    """Test that match_importer finds fuzzy name match above 85% threshold."""
    # Create importer
    importer = Importer(
        id=uuid4(),
        tax_code="9876543210",
        name="ABC Trading Company Limited",
        name_normalized="abc trading company limited",
        organization_id=test_organization.id,
        declaration_count=3,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(importer)
    await db_session.commit()

    # Test with very similar name (one word different)
    result = await match_importer(
        extracted_tax_code=None,
        extracted_name="ABC Trading Company Ltd",  # "Limited" vs "Ltd"
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is not None
    assert result.id == importer.id


@pytest.mark.asyncio
async def test_match_importer_fuzzy_name_match_below_threshold(db_session, test_organization):
    """Test that match_importer returns None for similarity below 85%."""
    # Create importer
    importer = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="ABC Company",
        name_normalized="abc company",
        organization_id=test_organization.id,
        declaration_count=1,
        is_verified=False,
        confidence_score=0.7,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(importer)
    await db_session.commit()

    # Test with very different name
    result = await match_importer(
        extracted_tax_code=None,
        extracted_name="Totally Different Company Name XYZ",
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_importer_prefers_tax_code_over_name(db_session, test_organization):
    """Test that match_importer prefers exact tax_code match over fuzzy name."""
    # Create two importers
    importer1 = Importer(
        id=uuid4(),
        tax_code="1234567890",
        name="Company A",
        name_normalized="company a",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=1.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    importer2 = Importer(
        id=uuid4(),
        tax_code="9999999999",
        name="Test Company ABC",  # Very similar name to search
        name_normalized="test company abc",
        organization_id=test_organization.id,
        declaration_count=2,
        is_verified=False,
        confidence_score=0.8,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([importer1, importer2])
    await db_session.commit()

    # Search with tax_code matching importer1 but name similar to importer2
    result = await match_importer(
        extracted_tax_code="1234567890",
        extracted_name="Test Company ABC Ltd",  # Similar to importer2
        organization_id=test_organization.id,
        db=db_session
    )

    # Should match importer1 by tax_code (priority)
    assert result is not None
    assert result.id == importer1.id


@pytest.mark.asyncio
async def test_match_importer_ignores_deleted(db_session, test_organization):
    """Test that match_importer ignores soft-deleted importers."""
    # Create deleted importer
    importer = Importer(
        id=uuid4(),
        tax_code="5555555555",
        name="Deleted Company",
        name_normalized="deleted company",
        organization_id=test_organization.id,
        declaration_count=0,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted_at=datetime.utcnow()  # Soft deleted
    )
    db_session.add(importer)
    await db_session.commit()

    # Should not find deleted importer
    result = await match_importer(
        extracted_tax_code="5555555555",
        extracted_name=None,
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_importer_organization_isolation(db_session, test_organization):
    """Test that match_importer respects organization_id filtering."""
    # Create importer in different organization
    other_org_id = UUID("00000000-0000-0000-0000-000000000099")
    importer = Importer(
        id=uuid4(),
        tax_code="7777777777",
        name="Other Org Company",
        name_normalized="other org company",
        organization_id=other_org_id,  # Different org
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(importer)
    await db_session.commit()

    # Should not find importer from different organization
    result = await match_importer(
        extracted_tax_code="7777777777",
        extracted_name="Other Org Company",
        organization_id=test_organization.id,  # Searching in test_organization
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_importer_returns_none_when_no_input(db_session, test_organization):
    """Test that match_importer returns None when no tax_code or name provided."""
    result = await match_importer(
        extracted_tax_code=None,
        extracted_name=None,
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_importer_selects_best_fuzzy_match(db_session, test_organization):
    """Test that match_importer selects the best fuzzy match when multiple candidates."""
    # Create three importers with varying similarity
    importer1 = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="ABC Company Limited",
        name_normalized="abc company limited",
        organization_id=test_organization.id,
        declaration_count=1,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    importer2 = Importer(
        id=uuid4(),
        tax_code="2222222222",
        name="ABC Company Ltd",  # Closer match
        name_normalized="abc company ltd",
        organization_id=test_organization.id,
        declaration_count=2,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    importer3 = Importer(
        id=uuid4(),
        tax_code="3333333333",
        name="XYZ Corporation",  # Very different
        name_normalized="xyz corporation",
        organization_id=test_organization.id,
        declaration_count=1,
        is_verified=False,
        confidence_score=0.7,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([importer1, importer2, importer3])
    await db_session.commit()

    # Search with name closest to importer2
    result = await match_importer(
        extracted_tax_code=None,
        extracted_name="ABC Company Ltd",
        organization_id=test_organization.id,
        db=db_session
    )

    # Should find best match (exact or highest similarity)
    assert result is not None
    # importer2 should have highest similarity
    assert result.tax_code == "2222222222"


# ========================================
# Test match_exporter (async)
# ========================================

@pytest.mark.asyncio
async def test_match_exporter_exact_name_and_country_match(db_session, test_organization):
    """Test that match_exporter finds exact name_normalized + country_code match."""
    # Create exporter
    exporter = Exporter(
        id=uuid4(),
        name="China Export Company",
        name_normalized="china export company",
        country_code="CN",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=0.98,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(exporter)
    await db_session.commit()

    # Test with exact match
    result = await match_exporter(
        extracted_name="China Export Company",
        extracted_country_code="CN",
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is not None
    assert result.id == exporter.id


@pytest.mark.asyncio
async def test_match_exporter_fuzzy_name_match_same_country(db_session, test_organization):
    """Test that match_exporter finds fuzzy name match within same country."""
    # Create exporter
    exporter = Exporter(
        id=uuid4(),
        name="US Trading Company Limited",
        name_normalized="us trading company limited",
        country_code="US",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.92,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(exporter)
    await db_session.commit()

    # Test with similar name, same country
    result = await match_exporter(
        extracted_name="US Trading Company Ltd",  # "Limited" vs "Ltd"
        extracted_country_code="US",
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is not None
    assert result.id == exporter.id


@pytest.mark.asyncio
async def test_match_exporter_fuzzy_name_match_below_threshold(db_session, test_organization):
    """Test that match_exporter returns None for similarity below 85%."""
    # Create exporter
    exporter = Exporter(
        id=uuid4(),
        name="German GmbH Company",
        name_normalized="german gmbh company",
        country_code="DE",
        organization_id=test_organization.id,
        declaration_count=2,
        is_verified=False,
        confidence_score=0.8,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(exporter)
    await db_session.commit()

    # Test with very different name
    result = await match_exporter(
        extracted_name="Completely Different Business Name",
        extracted_country_code="DE",
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_exporter_prefers_exact_over_fuzzy(db_session, test_organization):
    """Test that match_exporter prefers exact match over fuzzy match."""
    # Create two exporters
    exporter1 = Exporter(
        id=uuid4(),
        name="ABC Corp",
        name_normalized="abc corp",
        country_code="CN",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=1.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    exporter2 = Exporter(
        id=uuid4(),
        name="ABC Corporation Limited",  # Similar but not exact
        name_normalized="abc corporation limited",
        country_code="CN",
        organization_id=test_organization.id,
        declaration_count=2,
        is_verified=False,
        confidence_score=0.85,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([exporter1, exporter2])
    await db_session.commit()

    # Search with exact match to exporter1
    result = await match_exporter(
        extracted_name="ABC Corp",
        extracted_country_code="CN",
        organization_id=test_organization.id,
        db=db_session
    )

    # Should find exact match (exporter1)
    assert result is not None
    assert result.id == exporter1.id


@pytest.mark.asyncio
async def test_match_exporter_ignores_deleted(db_session, test_organization):
    """Test that match_exporter ignores soft-deleted exporters."""
    # Create deleted exporter
    exporter = Exporter(
        id=uuid4(),
        name="Deleted Exporter",
        name_normalized="deleted exporter",
        country_code="JP",
        organization_id=test_organization.id,
        declaration_count=0,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted_at=datetime.utcnow()  # Soft deleted
    )
    db_session.add(exporter)
    await db_session.commit()

    # Should not find deleted exporter
    result = await match_exporter(
        extracted_name="Deleted Exporter",
        extracted_country_code="JP",
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_exporter_organization_isolation(db_session, test_organization):
    """Test that match_exporter respects organization_id filtering."""
    # Create exporter in different organization
    other_org_id = UUID("00000000-0000-0000-0000-000000000099")
    exporter = Exporter(
        id=uuid4(),
        name="Other Org Exporter",
        name_normalized="other org exporter",
        country_code="KR",
        organization_id=other_org_id,  # Different org
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(exporter)
    await db_session.commit()

    # Should not find exporter from different organization
    result = await match_exporter(
        extracted_name="Other Org Exporter",
        extracted_country_code="KR",
        organization_id=test_organization.id,  # Searching in test_organization
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_exporter_returns_none_when_no_name(db_session, test_organization):
    """Test that match_exporter returns None when no name provided."""
    result = await match_exporter(
        extracted_name=None,
        extracted_country_code="US",
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is None


@pytest.mark.asyncio
async def test_match_exporter_fuzzy_without_country_code(db_session, test_organization):
    """Test that match_exporter can do fuzzy matching without country_code."""
    # Create exporter
    exporter = Exporter(
        id=uuid4(),
        name="Global Trading Inc",
        name_normalized="global trading inc",
        country_code="US",
        organization_id=test_organization.id,
        declaration_count=3,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(exporter)
    await db_session.commit()

    # Search without country_code (fuzzy match across all countries)
    result = await match_exporter(
        extracted_name="Global Trading Inc",
        extracted_country_code=None,  # No country filter
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is not None
    assert result.id == exporter.id


@pytest.mark.asyncio
async def test_match_exporter_country_code_case_insensitive(db_session, test_organization):
    """Test that match_exporter handles country_code case-insensitively."""
    # Create exporter with uppercase country code
    exporter = Exporter(
        id=uuid4(),
        name="French Company",
        name_normalized="french company",
        country_code="FR",  # Uppercase
        organization_id=test_organization.id,
        declaration_count=2,
        is_verified=True,
        confidence_score=0.88,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(exporter)
    await db_session.commit()

    # Search with lowercase country code
    result = await match_exporter(
        extracted_name="French Company",
        extracted_country_code="fr",  # Lowercase
        organization_id=test_organization.id,
        db=db_session
    )

    assert result is not None
    assert result.id == exporter.id


@pytest.mark.asyncio
async def test_match_exporter_selects_best_fuzzy_match(db_session, test_organization):
    """Test that match_exporter selects the best fuzzy match."""
    # Create multiple exporters with varying similarity
    exporter1 = Exporter(
        id=uuid4(),
        name="ABC Trading Company Limited",
        name_normalized="abc trading company limited",
        country_code="CN",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    exporter2 = Exporter(
        id=uuid4(),
        name="ABC Trading Company Ltd",  # Closer match
        name_normalized="abc trading company ltd",
        country_code="CN",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    exporter3 = Exporter(
        id=uuid4(),
        name="XYZ Manufacturing Corp",  # Very different
        name_normalized="xyz manufacturing corp",
        country_code="CN",
        organization_id=test_organization.id,
        declaration_count=2,
        is_verified=False,
        confidence_score=0.7,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([exporter1, exporter2, exporter3])
    await db_session.commit()

    # Search with name closest to exporter2
    result = await match_exporter(
        extracted_name="ABC Trading Company Ltd",
        extracted_country_code="CN",
        organization_id=test_organization.id,
        db=db_session
    )

    # Should find best match (exact or highest similarity)
    assert result is not None
    assert result.name_normalized == "abc trading company ltd"
