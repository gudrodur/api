import pytest
from httpx import AsyncClient

# ----------------------------------
# Fixtures assumed:
# - async_client (from conftest.py)
# - test_user_token (user role)
# - admin_token (admin role)
# ----------------------------------

VALID_STATUSES = [
    "New",
    "Exclusive Lock",
    "Follow Up",
    "Closed",
    "Unreachable",
    "Do Not Contact"
]

INVALID_STATUSES = [
    "exclusive_lock",      # Wrong case
    "EXCLUSIVE LOCK",      # All caps
    "Locked",              # Not in enum
    "Pending",             # Not allowed
    "Exclusive  Lock",     # Extra spaces
]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", VALID_STATUSES)
async def test_create_valid_contact_status(async_client: AsyncClient, admin_token: str, status: str):
    """✅ Admin can create valid contact statuses."""
    response = await async_client.post(
        "/contact_status/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": status}
    )
    # Allow 400 if already exists from previous test
    assert response.status_code in (200, 201, 400)
    if response.status_code == 400:
        assert "already exists" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("status", INVALID_STATUSES)
async def test_create_invalid_enum_status_fails(async_client: AsyncClient, admin_token: str, status: str):
    """❌ Admin cannot create non-enum status values."""
    response = await async_client.post(
        "/contact_status/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": status}
    )
    assert response.status_code == 422
    assert "not allowed" in response.text.lower()


@pytest.mark.asyncio
async def test_prevent_duplicate_status(async_client: AsyncClient, admin_token: str):
    """❌ Should reject duplicate contact statuses."""
    payload = {"name": "Closed"}

    # First attempt
    first = await async_client.post(
        "/contact_status/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload
    )
    assert first.status_code in (200, 201, 400)

    # Second attempt - must fail
    second = await async_client.post(
        "/contact_status/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload
    )
    assert second.status_code == 400
    assert "already exists" in second.text


@pytest.mark.asyncio
async def test_user_cannot_create_status(async_client: AsyncClient, test_user_token: str):
    """❌ Normal users cannot create new statuses."""
    response = await async_client.post(
        "/contact_status/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "New"}
    )
    assert response.status_code == 403
