import json
import logging
import sys

from apps.core.logging import JsonFormatter, RequestIdFilter
from apps.core.middleware import current_request_id


def record(message: str, **extra: object) -> logging.LogRecord:
    log_record = logging.LogRecord(
        'apps.accounts', logging.WARNING, __file__, 1, message, None, None
    )
    log_record.__dict__.update(extra)
    RequestIdFilter().filter(log_record)
    return log_record


def test_every_line_carries_the_request_id_of_its_request():
    token = current_request_id.set('a1b2c3')
    try:
        log_record = record('sign-up rate limited')
    finally:
        current_request_id.reset(token)

    assert log_record.request_id == 'a1b2c3'


def test_writes_one_json_line_with_its_fields_and_extras():
    line = JsonFormatter().format(record('request', status=201, path='/api/v1/x/'))

    event = json.loads(line)
    assert '\n' not in line
    assert event['time'].endswith('Z')
    assert {key: event[key] for key in ('level', 'logger', 'message', 'status')} == {
        'level': 'WARNING',
        'logger': 'apps.accounts',
        'message': 'request',
        'status': 201,
    }


def test_keeps_a_traceback_inside_its_own_event():
    try:
        raise RuntimeError('boom')
    except RuntimeError:
        log_record = record('unhandled exception')
        log_record.exc_info = sys.exc_info()

    line = JsonFormatter().format(log_record)

    assert '\n' not in line
    assert 'RuntimeError: boom' in json.loads(line)['exc_info']
