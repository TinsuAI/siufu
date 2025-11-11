"""
Unit tests for Companies API endpoints

Tests for:
- GET /api/companies/ - List companies with pagination, search, filter
- GET /api/companies/{id} - Get company details
- POST /api/companies/ - Create company
- PATCH /api/companies/{id} - Update company
- DELETE /api/companies/{id} - Soft delete company
- GET /api/companies/duplicates - Find duplicates
- POST /api/companies/merge - Merge companies
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.models.importer import Importer

# ========================================
# Test list_companies endpoint
# ========================================

@pytest.mark.asyncio
async def test_list_importers_success(db_session, test_user, test_organization, async_client):
    """Test listing importers with pagination."""
    # Create test importers
    importer1 = Importer(
        id=uuid4(),
        tax_code="1234567890",
        name="Company A",
        name_normalized="company a",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=1.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer2 = Importer(
        id=uuid4(),
        tax_code="0987654321",
        name="Company B",
        name_normalized="company b",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=False,
        confidence_score=0.8,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([importer1, importer2])
    await db_session.commit()

    # Make authenticated request
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        "/api/companies/?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_companies_with_search(db_session, test_user, test_organization, async_client):
    """Test listing companies with search filter."""
    # Create test importers
    importer1 = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="ABC Trading Company",
        name_normalized="abc trading company",
        organization_id=test_organization.id,
        declaration_count=3,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer2 = Importer(
        id=uuid4(),
        tax_code="2222222222",
        name="XYZ Corporation",
        name_normalized="xyz corporation",
        organization_id=test_organization.id,
        declaration_count=1,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([importer1, importer2])
    await db_session.commit()

    # Make authenticated request with search
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        "/api/companies/?type=importers&search=ABC",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "ABC Trading Company"


@pytest.mark.asyncio
async def test_list_companies_filter_verified(db_session, test_user, test_organization, async_client):
    """Test listing companies with verified filter."""
    # Create mixed verification status
    importer1 = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="Verified Company",
        name_normalized="verified company",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=1.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer2 = Importer(
        id=uuid4(),
        tax_code="2222222222",
        name="Unverified Company",
        name_normalized="unverified company",
        organization_id=test_organization.id,
        declaration_count=1,
        is_verified=False,
        confidence_score=0.7,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([importer1, importer2])
    await db_session.commit()

    # Make authenticated request with verified filter
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        "/api/companies/?type=importers&filter=verified",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["is_verified"] is True


@pytest.mark.asyncio
async def test_list_companies_ignores_deleted(db_session, test_user, test_organization, async_client):
    """Test that list_companies ignores soft-deleted companies."""
    # Create one active and one deleted importer
    importer_active = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="Active Company",
        name_normalized="active company",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer_deleted = Importer(
        id=uuid4(),
        tax_code="2222222222",
        name="Deleted Company",
        name_normalized="deleted company",
        organization_id=test_organization.id,
        declaration_count=2,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc)  # Soft deleted
    )
    db_session.add_all([importer_active, importer_deleted])
    await db_session.commit()

    # Make authenticated request
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        "/api/companies/?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1  # Only active company
    assert data["items"][0]["name"] == "Active Company"


@pytest.mark.asyncio
async def test_list_companies_organization_isolation(db_session, test_user, test_organization, async_client):
    """Test that list_companies respects organization_id filtering."""
    # Create importer in different organization
    other_org_id = uuid4()
    importer_other_org = Importer(
        id=uuid4(),
        tax_code="9999999999",
        name="Other Org Company",
        name_normalized="other org company",
        organization_id=other_org_id,  # Different org
        declaration_count=10,
        is_verified=True,
        confidence_score=1.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer_my_org = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="My Org Company",
        name_normalized="my org company",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([importer_other_org, importer_my_org])
    await db_session.commit()

    # Make authenticated request
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        "/api/companies/?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1  # Only my org's company
    assert data["items"][0]["name"] == "My Org Company"


# ========================================
# Test get_company endpoint
# ========================================

@pytest.mark.asyncio
async def test_get_company_success(db_session, test_user, test_organization, async_client):
    """Test getting company details by ID."""
    # Create test importer
    importer = Importer(
        id=uuid4(),
        tax_code="1234567890",
        name="Test Company",
        name_normalized="test company",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(importer)
    await db_session.commit()

    # Make authenticated request
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        f"/api/companies/{importer.id}?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(importer.id)
    assert data["name"] == "Test Company"


@pytest.mark.asyncio
async def test_get_company_not_found(db_session, test_user, async_client):
    """Test getting non-existent company returns 404."""
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    non_existent_id = uuid4()
    response = await async_client.get(
        f"/api/companies/{non_existent_id}?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_company_wrong_organization(db_session, test_user, async_client):
    """Test getting company from different organization returns 403."""
    # Create importer in different organization
    other_org_id = uuid4()
    importer = Importer(
        id=uuid4(),
        tax_code="1234567890",
        name="Other Org Company",
        name_normalized="other org company",
        organization_id=other_org_id,  # Different org
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(importer)
    await db_session.commit()

    # Make authenticated request
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        f"/api/companies/{importer.id}?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 403


# ========================================
# Test create_company endpoint
# ========================================

@pytest.mark.asyncio
async def test_create_importer_success(db_session, test_user, async_client):
    """Test creating a new importer."""
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    importer_data = {
        "tax_code": "1234-567-890",  # Will be normalized
        "name": "New Test Company",
        "postal_code": "700000",
        "address": "123 Test Street",
        "phone": "+84 28 1234 5678"
    }

    response = await async_client.post(
        "/api/companies/?type=importers",
        json={"importer_data": importer_data},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["tax_code"] == "1234567890"  # Normalized
    assert data["name"] == "New Test Company"
    assert data["is_verified"] is True
    assert data["confidence_score"] == 1.0


@pytest.mark.asyncio
async def test_create_exporter_success(db_session, test_user, async_client):
    """Test creating a new exporter."""
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    exporter_data = {
        "name": "China Export Company",
        "country_code": "cn",  # Will be uppercased
        "address_line1": "123 Beijing Road",
        "address_line2": "Haidian District",
        "address_line3": "Beijing, China"
    }

    response = await async_client.post(
        "/api/companies/?type=exporters",
        json={"exporter_data": exporter_data},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["country_code"] == "CN"  # Uppercased
    assert data["name"] == "China Export Company"
    assert data["is_verified"] is True


# ========================================
# Test update_company endpoint
# ========================================

@pytest.mark.asyncio
async def test_update_importer_success(db_session, test_user, test_organization, async_client):
    """Test updating an importer."""
    # Create importer
    importer = Importer(
        id=uuid4(),
        tax_code="1234567890",
        name="Original Name",
        name_normalized="original name",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(importer)
    await db_session.commit()

    # Update
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    update_data = {
        "name": "Updated Name",
        "address": "New Address 456"
    }

    response = await async_client.patch(
        f"/api/companies/{importer.id}?type=importers",
        json={"importer_data": update_data},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["address"] == "New Address 456"


@pytest.mark.asyncio
async def test_update_company_not_found(db_session, test_user, async_client):
    """Test updating non-existent company returns 404."""
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    non_existent_id = uuid4()
    response = await async_client.patch(
        f"/api/companies/{non_existent_id}?type=importers",
        json={"importer_data": {"name": "Test"}},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 404


# ========================================
# Test delete_company endpoint
# ========================================

@pytest.mark.asyncio
async def test_delete_company_soft_delete(db_session, test_user, test_organization, async_client):
    """Test soft deleting a company."""
    # Create importer
    importer = Importer(
        id=uuid4(),
        tax_code="1234567890",
        name="To Delete Company",
        name_normalized="to delete company",
        organization_id=test_organization.id,
        declaration_count=0,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(importer)
    await db_session.commit()

    # Delete

    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.delete(
        f"/api/companies/{importer.id}?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 204

    # Verify soft delete (deleted_at should be set)
    await db_session.refresh(importer)
    assert importer.deleted_at is not None


# ========================================
# Test get_duplicates endpoint
# ========================================

@pytest.mark.asyncio
async def test_get_duplicates_finds_similar_names(db_session, test_user, test_organization, async_client):
    """Test finding duplicate companies with similar names."""
    # Create similar importers (>80% similarity)
    importer1 = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="ABC Trading Company Limited",
        name_normalized="abc trading company limited",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer2 = Importer(
        id=uuid4(),
        tax_code="2222222222",
        name="ABC Trading Company Ltd",  # Very similar
        name_normalized="abc trading company ltd",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([importer1, importer2])
    await db_session.commit()

    # Get duplicates
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        "/api/companies/duplicates/?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1  # Should find at least one duplicate pair
    assert data[0]["similarity"] >= 0.80


@pytest.mark.asyncio
async def test_get_duplicates_no_matches(db_session, test_user, test_organization, async_client):
    """Test get_duplicates returns empty list when no duplicates."""
    # Create very different importers
    importer1 = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="ABC Company",
        name_normalized="abc company",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer2 = Importer(
        id=uuid4(),
        tax_code="2222222222",
        name="XYZ Corporation Totally Different",
        name_normalized="xyz corporation totally different",
        organization_id=test_organization.id,
        declaration_count=3,
        is_verified=True,
        confidence_score=0.9,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([importer1, importer2])
    await db_session.commit()

    # Get duplicates
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    response = await async_client.get(
        "/api/companies/duplicates/?type=importers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # No duplicates


# ========================================
# Test merge_companies endpoint
# ========================================

@pytest.mark.asyncio
async def test_merge_companies_success(db_session, test_user, test_organization, async_client):
    """Test merging two companies."""
    # Create two importers
    importer_keep = Importer(
        id=uuid4(),
        tax_code="1111111111",
        name="Company to Keep",
        name_normalized="company to keep",
        organization_id=test_organization.id,
        declaration_count=10,
        is_verified=True,
        confidence_score=0.95,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    importer_merge = Importer(
        id=uuid4(),
        tax_code="2222222222",
        name="Company to Merge",
        name_normalized="company to merge",
        organization_id=test_organization.id,
        declaration_count=5,
        is_verified=False,
        confidence_score=0.8,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([importer_keep, importer_merge])
    await db_session.commit()

    # Merge
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    merge_request = {
        "keep_id": str(importer_keep.id),
        "merge_id": str(importer_merge.id)
    }

    response = await async_client.post(
        "/api/companies/merge/?type=importers",
        json=merge_request,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(importer_keep.id)
    assert data["declaration_count"] == 15  # 10 + 5

    # Verify merge_company is soft deleted
    await db_session.refresh(importer_merge)
    assert importer_merge.deleted_at is not None


@pytest.mark.asyncio
async def test_merge_companies_same_id_fails(db_session, test_user, async_client):
    """Test merging a company with itself fails."""
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    same_id = uuid4()
    merge_request = {
        "keep_id": str(same_id),
        "merge_id": str(same_id)
    }

    response = await async_client.post(
        "/api/companies/merge/?type=importers",
        json=merge_request,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_merge_companies_not_found(db_session, test_user, async_client):
    """Test merging non-existent companies fails."""
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": str(test_user.id)})

    merge_request = {
        "keep_id": str(uuid4()),
        "merge_id": str(uuid4())
    }

    response = await async_client.post(
        "/api/companies/merge/?type=importers",
        json=merge_request,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 404
