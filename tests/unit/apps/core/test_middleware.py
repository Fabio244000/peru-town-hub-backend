import logging
from http import HTTPStatus

import pytest
from django.http import HttpRequest, HttpResponse

from apps.core.middleware import RequestIdMiddleware, current_request_id

SAFE_REQUEST_ID = '3f2c9a1e-request-id'


def answer(request: HttpRequest) -> HttpResponse:
    return HttpResponse(current_request_id.get(), status=HTTPStatus.CREATED)


def call(rf, **headers):
    request = rf.get('/api/v1/accounts/username-availability/?username=rosa', **headers)
    return RequestIdMiddleware(answer)(request)


def test_creates_a_request_id_and_sends_it_in_the_response(rf):
    response = call(rf)

    assert response['X-Request-ID']
    assert response.content.decode() == response['X-Request-ID']


def test_keeps_a_safe_request_id_sent_by_the_client(rf):
    response = call(rf, HTTP_X_REQUEST_ID=SAFE_REQUEST_ID)

    assert response['X-Request-ID'] == SAFE_REQUEST_ID


@pytest.mark.parametrize('unsafe', ['x' * 65, 'abc\ninjected', 'id with spaces', ''])
def test_replaces_a_request_id_that_is_not_safe(rf, unsafe):
    response = call(rf, HTTP_X_REQUEST_ID=unsafe)

    assert response['X-Request-ID'] != unsafe


def test_logs_one_line_per_request_without_the_query_string(rf, caplog):
    with caplog.at_level(logging.INFO, logger='apps.core.requests'):
        response = call(rf, HTTP_X_REQUEST_ID=SAFE_REQUEST_ID)

    [record] = caplog.records
    assert (record.method, record.path, record.status, record.request_id) == (
        'GET',
        '/api/v1/accounts/username-availability/',
        HTTPStatus.CREATED,
        response['X-Request-ID'],
    )
    assert record.duration_ms >= 0
    assert 'rosa' not in caplog.text


def test_forgets_the_request_id_when_the_request_ends(rf):
    call(rf, HTTP_X_REQUEST_ID=SAFE_REQUEST_ID)

    assert current_request_id.get() != SAFE_REQUEST_ID
