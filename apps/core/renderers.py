from typing import Any

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class EnvelopeJSONRenderer(JSONRenderer):
    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        response = (renderer_context or {}).get('response')
        if response is not None and self._is_success_with_body(response):
            data = self._envelope(data, response)
        return super().render(data, accepted_media_type, renderer_context)

    @staticmethod
    def _is_success_with_body(response: Response) -> bool:
        return (
            status.is_success(response.status_code)
            and response.status_code != status.HTTP_204_NO_CONTENT
        )

    @staticmethod
    def _envelope(data: Any, response: Response) -> dict[str, Any]:
        return {
            'success': True,
            'message': getattr(response, 'message', ''),
            'data': data,
            'detail': None,
        }
