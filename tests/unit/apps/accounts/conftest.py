from collections.abc import Callable
from typing import Any

import pytest

from apps.accounts.models import User


@pytest.fixture
def stored_account() -> Callable[[str], dict[str, Any] | None]:
    """The only place of these tests that reads the model."""

    def read(username: str) -> dict[str, Any] | None:
        user = User.objects.filter(username=username).first()
        if user is None:
            return None
        return {
            'uuid': user.uuid,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'password': user.password,
            'phone': user.phone,
            'phone_status': user.phone_status,
            'policies_accepted_at': user.policies_accepted_at,
            'date_joined': user.date_joined,
        }

    return read


@pytest.fixture
def count_accounts() -> Callable[[], int]:
    return User.objects.count
