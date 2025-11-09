"""
Master Data Service for matching and managing importers/exporters

This service provides functionality for:
- Normalizing company names and tax codes
- Calculating similarity between strings
- Matching importers and exporters against master data
"""
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.importer import Importer
from src.models.exporter import Exporter


def normalize_tax_code(tax_code: str) -> str:
    """
    Normalize tax code by removing spaces, dashes, and converting to uppercase.

    Args:
        tax_code: Raw tax code string

    Returns:
        Normalized tax code (alphanumeric uppercase only)

    Examples:
        >>> normalize_tax_code("0123-456-789")
        "0123456789"
        >>> normalize_tax_code("abc 123")
        "ABC123"
    """
    if not tax_code:
        return ""

    # Remove all non-alphanumeric characters
    normalized = re.sub(r'[^a-zA-Z0-9]', '', tax_code)

    # Convert to uppercase
    return normalized.upper()


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for fuzzy matching.

    Normalization steps:
    1. Convert to lowercase
    2. Remove accents/diacritics (Vietnamese characters)
    3. Remove special characters (keep only letters, numbers, spaces)
    4. Collapse multiple spaces to single space
    5. Trim leading/trailing spaces

    Args:
        name: Raw company name

    Returns:
        Normalized company name

    Examples:
        >>> normalize_company_name("Công ty TNHH ABC")
        "cong ty tnhh abc"
        >>> normalize_company_name("  Company   (USA)  ")
        "company usa"
    """
    if not name:
        return ""

    # Convert to lowercase
    normalized = name.lower()

    # Remove accents (NFKD normalization)
    # This converts "Công" to "Cong"
    normalized = unicodedata.normalize('NFKD', normalized)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])

    # Remove special characters, keep only alphanumeric and spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

    # Collapse multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)

    # Trim
    return normalized.strip()


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate Levenshtein distance similarity ratio between two strings.

    Uses Python's difflib.SequenceMatcher which implements a variation of the
    Ratcliff/Obershelp algorithm.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity ratio from 0.0 (completely different) to 1.0 (identical)

    Examples:
        >>> calculate_similarity("hello", "hello")
        1.0
        >>> calculate_similarity("hello", "world")
        0.2
        >>> calculate_similarity("company abc", "company xyz")
        0.73
    """
    if not str1 or not str2:
        return 0.0

    return SequenceMatcher(None, str1, str2).ratio()


async def match_importer(
    extracted_tax_code: Optional[str],
    extracted_name: Optional[str],
    organization_id: UUID,
    db: AsyncSession
) -> Optional[Importer]:
    """
    Match importer against master data using tax code and fuzzy name matching.

    Matching strategy:
    1. Primary: Exact tax_code match (most reliable)
    2. Fallback: Fuzzy name match with 85%+ similarity

    Args:
        extracted_tax_code: Tax code from AI extraction
        extracted_name: Company name from AI extraction
        organization_id: Organization ID for filtering
        db: Database session

    Returns:
        Matched Importer or None if no match found
    """
    if not extracted_tax_code and not extracted_name:
        return None

    # Strategy 1: Exact tax_code match
    if extracted_tax_code:
        normalized_tax_code = normalize_tax_code(extracted_tax_code)

        stmt = select(Importer).where(
            Importer.organization_id == organization_id,
            Importer.tax_code == normalized_tax_code,
            Importer.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        importer = result.scalars().first()

        if importer:
            return importer

    # Strategy 2: Fuzzy name match (85% threshold)
    if extracted_name:
        normalized_name = normalize_company_name(extracted_name)

        # Fetch all non-deleted importers for this organization
        stmt = select(Importer).where(
            Importer.organization_id == organization_id,
            Importer.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        importers = result.scalars().all()

        # Find best match above threshold
        best_match = None
        best_similarity = 0.85  # Threshold

        for importer in importers:
            similarity = calculate_similarity(normalized_name, importer.name_normalized)
            if similarity >= best_similarity:
                best_similarity = similarity
                best_match = importer

        return best_match

    return None


async def match_exporter(
    extracted_name: Optional[str],
    extracted_country_code: Optional[str],
    organization_id: UUID,
    db: AsyncSession
) -> Optional[Exporter]:
    """
    Match exporter against master data using exact and fuzzy name matching.

    Matching strategy:
    1. Primary: Exact name_normalized + country_code match
    2. Fallback: Fuzzy name match within same country (85%+ similarity)

    Args:
        extracted_name: Company name from AI extraction
        extracted_country_code: ISO country code (e.g., "CN", "US")
        organization_id: Organization ID for filtering
        db: Database session

    Returns:
        Matched Exporter or None if no match found
    """
    if not extracted_name:
        return None

    normalized_name = normalize_company_name(extracted_name)

    # Strategy 1: Exact match (name_normalized + country_code)
    if extracted_country_code:
        stmt = select(Exporter).where(
            Exporter.organization_id == organization_id,
            Exporter.name_normalized == normalized_name,
            Exporter.country_code == extracted_country_code.upper(),
            Exporter.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        exporter = result.scalars().first()

        if exporter:
            return exporter

    # Strategy 2: Fuzzy name match within same country (85% threshold)
    # Filter by country if available, otherwise search all
    filters = [
        Exporter.organization_id == organization_id,
        Exporter.deleted_at.is_(None)
    ]

    if extracted_country_code:
        filters.append(Exporter.country_code == extracted_country_code.upper())

    stmt = select(Exporter).where(*filters)
    result = await db.execute(stmt)
    exporters = result.scalars().all()

    # Find best match above threshold
    best_match = None
    best_similarity = 0.85  # Threshold

    for exporter in exporters:
        similarity = calculate_similarity(normalized_name, exporter.name_normalized)
        if similarity >= best_similarity:
            best_similarity = similarity
            best_match = exporter

    return best_match
