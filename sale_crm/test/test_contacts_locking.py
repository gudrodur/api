import pytest


@pytest.mark.asyncio
async def test_lock_and_unlock_contact(async_client, test_user_token, test_contact_id):
    """
    ✅ Test that a user can lock and unlock a contact successfully.
    """
    token = test_user_token  # ⛔️ Do not await: it's already a string
    contact_id = test_contact_id  # ⛔️ Do not await: it's already an int
    headers = {"Authorization": f"Bearer {token}"}

    # Lock the contact
    lock_res = await async_client.patch(
        f"/contacts/{contact_id}/status",
        json={"status_name": "Exclusive Lock"},
        headers=headers
    )
    assert lock_res.status_code == 204, f"Lock failed: {lock_res.status_code}, {lock_res.text}"

    # Verify it's in the locked list
    locked_res = await async_client.get("/contacts/locked", headers=headers)
    assert locked_res.status_code == 200, f"Failed to fetch locked contacts: {locked_res.status_code}"
    locked_ids = [c["id"] for c in locked_res.json()]
    assert contact_id in locked_ids, f"Contact {contact_id} should be in locked list but is not."

    # Unlock the contact
    unlock_res = await async_client.patch(
        f"/contacts/{contact_id}/status",
        json={"status_name": "New"},
        headers=headers
    )
    assert unlock_res.status_code == 204, f"Unlock failed: {unlock_res.status_code}, {unlock_res.text}"


@pytest.mark.asyncio
async def test_forbid_unlock_by_other_user(
    async_client,
    db_session,
    test_contact_id,
    test_user_token,
    another_user_token
):
    """
    🚫 Test that a different user can't unlock a contact locked by another user.
    """
    contact_id = test_contact_id  # ⛔️ Already resolved int

    # Lock the contact with the first user
    token_owner = test_user_token
    headers_owner = {"Authorization": f"Bearer {token_owner}"}
    res_lock = await async_client.patch(
        f"/contacts/{contact_id}/status",
        json={"status_name": "Exclusive Lock"},
        headers=headers_owner
    )
    assert res_lock.status_code == 204, f"Initial lock failed: {res_lock.status_code}"

    # Try to unlock with another user
    token_other = another_user_token
    headers_other = {"Authorization": f"Bearer {token_other}"}
    res = await async_client.patch(
        f"/contacts/{contact_id}/status",
        json={"status_name": "New"},
        headers=headers_other
    )
    assert res.status_code == 403, f"Expected 403 Forbidden but got {res.status_code}"
