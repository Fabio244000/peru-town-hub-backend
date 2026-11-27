from typing import ClassVar
from uuid import uuid4

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from apps.accounts.constants import (
    PERSON_NAME_LENGTH,
    PHONE_LABEL,
    PHONE_MAX_LENGTH,
    PHONE_STATUS_LABEL,
    POLICIES_ACCEPTED_AT_LABEL,
    USERNAME_LENGTH,
    USERNAME_PATTERN,
    UUID_LABEL,
    PhoneStatus,
)
from apps.accounts.validators import (
    validate_person_name,
    validate_phone,
    validate_username,
)


class AccountUserManager(UserManager):
    @classmethod
    def normalize_email(cls, email: str | None) -> str | None:  # type: ignore[override]
        # Django turns a missing email into '', which would break its uniqueness.
        return (email or '').strip().lower() or None


class User(AbstractUser):
    uuid = models.UUIDField(UUID_LABEL, default=uuid4, editable=False)
    username = models.CharField(
        _('username'), max_length=USERNAME_LENGTH[1], validators=[validate_username]
    )
    first_name = models.CharField(
        _('first name'),
        max_length=PERSON_NAME_LENGTH[1],
        blank=True,
        validators=[validate_person_name],
    )
    last_name = models.CharField(
        _('last name'),
        max_length=PERSON_NAME_LENGTH[1],
        blank=True,
        validators=[validate_person_name],
    )
    # Optional and unique: NULL, so several users without email do not clash.
    email = models.EmailField(  # type: ignore[assignment]  # noqa: DJ001
        _('email address'), null=True, blank=True
    )
    # Optional and unique: NULL, so several users without a cellphone do not clash.
    phone = models.CharField(  # noqa: DJ001
        PHONE_LABEL,
        max_length=PHONE_MAX_LENGTH,
        null=True,
        blank=True,
        validators=[validate_phone],
    )
    phone_status = models.CharField(
        PHONE_STATUS_LABEL,
        max_length=max(map(len, PhoneStatus.values)),
        choices=PhoneStatus.choices,
        blank=True,
    )
    policies_accepted_at = models.DateTimeField(
        POLICIES_ACCEPTED_AT_LABEL, null=True, blank=True
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects: ClassVar[AccountUserManager] = AccountUserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['uuid'], name='accounts_user_uuid_unique'),
            models.UniqueConstraint(
                fields=['username'], name='accounts_user_username_unique'
            ),
            models.CheckConstraint(
                condition=models.Q(username__regex=USERNAME_PATTERN),
                name='accounts_user_username_pattern',
            ),
            models.UniqueConstraint(
                fields=['email'], name='accounts_user_email_unique'
            ),
            models.CheckConstraint(
                condition=models.Q(email=Lower('email')),
                name='accounts_user_email_lowercase',
            ),
            models.UniqueConstraint(
                fields=['phone'], name='accounts_user_phone_unique'
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(phone__isnull=True, phone_status='')
                    | models.Q(phone__isnull=False, phone_status__in=PhoneStatus.values)
                ),
                name='accounts_user_phone_status_valid',
            ),
        ]
