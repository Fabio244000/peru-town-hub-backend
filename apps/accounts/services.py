from collections.abc import Callable
from datetime import datetime
from functools import partial

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.constants import (
    FIRST_NAMES_REQUIRED,
    LAST_NAMES_REQUIRED,
    PASSWORD_REQUIRED,
    PHONE_REQUIRED,
    PHONE_TAKEN,
    PHONE_TAKEN_CODE,
    USERNAME_REQUIRED,
    USERNAME_TAKEN,
    USERNAME_TAKEN_CODE,
    PhoneStatus,
)
from apps.accounts.dtos import NewAccount, RegisteredAccount, SessionTokens
from apps.accounts.models import User
from apps.accounts.validators import (
    normalize_person_name,
    validate_person_name,
    validate_phone,
    validate_username,
)
from apps.core.exceptions import ConflictError

# The business error of each unique constraint a duplicate (or a race) can break.
CONFLICTS = {
    'accounts_user_username_unique': (USERNAME_TAKEN, USERNAME_TAKEN_CODE),
    'accounts_user_phone_unique': (PHONE_TAKEN, PHONE_TAKEN_CODE),
}


class AccountRegistrationService:
    """Creates a person's account and signs them in."""

    @transaction.atomic
    def register(self, *, account: NewAccount) -> RegisteredAccount:
        now = timezone.now()
        user = self._build(account, now)
        self._validate(user, account)
        user.set_password(account.password)
        user.full_clean(validate_unique=False, validate_constraints=False)
        self._save(user)
        return self._registered(user)

    def _build(self, account: NewAccount, now: datetime) -> User:
        return User(
            username=account.username.strip(),
            first_name=normalize_person_name(account.first_names),
            last_name=normalize_person_name(account.last_names),
            phone=self._phone(account),
            phone_status=PhoneStatus.UNVERIFIED,
            policies_accepted_at=now,
            date_joined=now,
        )

    def _phone(self, account: NewAccount) -> str:
        """The cellphone in E.164: the country code and the number, joined."""
        number = account.phone_number.strip()
        country_code = account.phone_country_code.strip().removeprefix('+')
        return f'+{country_code}{number}' if number else ''

    def _validate(self, user: User, account: NewAccount) -> None:
        """Every field of the request with every rule it breaks, all at once."""
        # Per request field: its value, its message when missing and its validator.
        checks: dict[str, tuple[str, str, Callable[[str], None]]] = {
            'first_names': (
                user.first_name,
                FIRST_NAMES_REQUIRED,
                validate_person_name,
            ),
            'last_names': (user.last_name, LAST_NAMES_REQUIRED, validate_person_name),
            'username': (user.username, USERNAME_REQUIRED, validate_username),
            'password': (
                account.password,
                PASSWORD_REQUIRED,
                partial(validate_password, user=user),
            ),
            'phone_number': (user.phone or '', PHONE_REQUIRED, validate_phone),
        }
        errors = {
            field: messages
            for field, (value, required, validate) in checks.items()
            if (messages := self._broken_rules(value, required, validate))
        }
        if errors:
            raise ValidationError(errors)

    def _broken_rules(
        self, value: str, required: str, validate: Callable[[str], None]
    ) -> list[str]:
        if not value:
            return [required]
        try:
            validate(value)
        except ValidationError as error:
            return error.messages
        return []

    def _save(self, user: User) -> None:
        try:
            with transaction.atomic():
                user.save()
        except IntegrityError as error:
            conflict = CONFLICTS.get(_constraint_name(error) or '')
            if conflict is None:
                raise
            raise ConflictError(*conflict) from error

    def _registered(self, user: User) -> RegisteredAccount:
        return RegisteredAccount(
            username=user.username,
            first_names=user.first_name,
            last_names=user.last_name,
            phone=user.phone or '',
            phone_status=user.phone_status,
            created_at=user.date_joined,
            tokens=self._tokens(user),
        )

    def _tokens(self, user: User) -> SessionTokens:
        refresh = RefreshToken.for_user(user)
        return SessionTokens(
            access=str(refresh.access_token),
            refresh=str(refresh),
            expires_in=int(jwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
        )


def _constraint_name(error: IntegrityError) -> str | None:
    """The name PostgreSQL gives for the constraint the write broke."""
    diagnostics = getattr(error.__cause__, 'diag', None)
    return getattr(diagnostics, 'constraint_name', None)
