from drf_spectacular.utils import inline_serializer
from rest_framework import serializers


def success_envelope_schema(
    name: str, data: serializers.Field
) -> serializers.Serializer:
    return inline_serializer(
        name=name,
        fields={
            'success': serializers.BooleanField(),
            'message': serializers.CharField(allow_blank=True),
            'data': data,
            'detail': serializers.JSONField(allow_null=True),
        },
    )


def error_envelope_schema(
    name: str, detail: serializers.Field
) -> serializers.Serializer:
    return inline_serializer(
        name=name,
        fields={
            'success': serializers.BooleanField(),
            'message': serializers.CharField(),
            'data': serializers.JSONField(allow_null=True),
            'detail': detail,
        },
    )
