from rest_framework import serializers

from apps.accounts.constants import (
    FIRST_NAMES_REQUIRED,
    LAST_NAMES_REQUIRED,
    PASSWORD_REQUIRED,
    PHONE_REQUIRED,
    POLICIES_NOT_ACCEPTED,
    TOKEN_TYPE,
    USERNAME_REQUIRED,
)
from apps.accounts.dtos import RegisteredAccount
from apps.common.serializers import UtcDateTimeField


class AccountCreateInputSerializer(serializers.Serializer):
    """Types and presence only: the formats are the service's (with their messages)."""

    first_names = serializers.CharField(
        allow_blank=True, error_messages={'required': FIRST_NAMES_REQUIRED}
    )
    last_names = serializers.CharField(
        allow_blank=True, error_messages={'required': LAST_NAMES_REQUIRED}
    )
    username = serializers.CharField(
        allow_blank=True, error_messages={'required': USERNAME_REQUIRED}
    )
    # Not trimmed: a space at either end breaks R3 too.
    password = serializers.CharField(
        allow_blank=True,
        trim_whitespace=False,
        error_messages={'required': PASSWORD_REQUIRED},
    )
    phone_country_code = serializers.CharField()
    phone_number = serializers.CharField(
        allow_blank=True, error_messages={'required': PHONE_REQUIRED}
    )
    policies_accepted = serializers.BooleanField()

    def validate_policies_accepted(self, accepted: bool) -> bool:
        if not accepted:
            raise serializers.ValidationError(POLICIES_NOT_ACCEPTED)
        return accepted


class AccountCreateOutputSerializer(serializers.Serializer):
    username = serializers.CharField()
    first_names = serializers.CharField()
    last_names = serializers.CharField()
    phone = serializers.CharField()
    phone_status = serializers.CharField()
    created_at = UtcDateTimeField()
    access_token = serializers.CharField(source='tokens.access')
    refresh_token = serializers.CharField(source='tokens.refresh')
    token_type = serializers.SerializerMethodField()
    expires_in = serializers.IntegerField(source='tokens.expires_in')

    def get_token_type(self, account: RegisteredAccount) -> str:
        return TOKEN_TYPE


class UsernameAvailabilityInputSerializer(serializers.Serializer):
    username = serializers.CharField(
        allow_blank=True, error_messages={'required': USERNAME_REQUIRED}
    )


class UsernameAvailabilityOutputSerializer(serializers.Serializer):
    available = serializers.BooleanField()
