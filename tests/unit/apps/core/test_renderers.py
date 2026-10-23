import json
from http import HTTPStatus

from rest_framework.response import Response

from apps.core.renderers import EnvelopeJSONRenderer
from apps.core.responses import SuccessResponse

PAYLOAD = {'database': 'ok'}
SUCCESS_MESSAGE = 'El sistema está activo'


def render(response):
    content = EnvelopeJSONRenderer().render(
        response.data, renderer_context={'response': response}
    )
    return json.loads(content) if content else content


def test_success_response_is_wrapped_with_its_message():
    response = SuccessResponse(PAYLOAD, message=SUCCESS_MESSAGE)

    assert render(response) == {
        'success': True,
        'message': SUCCESS_MESSAGE,
        'data': PAYLOAD,
        'detail': None,
    }


def test_created_response_keeps_its_status_and_is_wrapped():
    response = SuccessResponse({'id': 1}, status=HTTPStatus.CREATED)

    assert response.status_code == HTTPStatus.CREATED
    assert render(response) == {
        'success': True,
        'message': '',
        'data': {'id': 1},
        'detail': None,
    }


def test_plain_drf_response_is_wrapped_with_empty_message():
    response = Response(PAYLOAD)

    assert render(response) == {
        'success': True,
        'message': '',
        'data': PAYLOAD,
        'detail': None,
    }


def test_error_response_is_rendered_as_is():
    envelope = {'success': False, 'message': 'Error', 'data': None, 'detail': None}
    response = Response(envelope, status=HTTPStatus.BAD_REQUEST)

    assert render(response) == envelope


def test_no_content_response_has_no_body():
    response = SuccessResponse(status=HTTPStatus.NO_CONTENT)

    assert render(response) == b''
