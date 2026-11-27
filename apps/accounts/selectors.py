from django.core.exceptions import ValidationError

from apps.accounts.constants import USERNAME_REQUIRED
from apps.accounts.models import User
from apps.accounts.validators import validate_username


def username_is_available(*, username: str) -> bool:
    """Whether a username can still be taken; one out of its format is rejected."""
    username = username.strip()
    try:
        if not username:
            raise ValidationError(USERNAME_REQUIRED)
        validate_username(username)
    except ValidationError as error:
        raise ValidationError({'username': error.messages}) from error
    return not User.objects.filter(username=username).exists()
