"""Every operation, with data generated from its own schema, answers what it documents.

Schemathesis runs in process against the WSGI app (rules/reference/api-docs.md).
"""

import pytest
import schemathesis
from django.core.signals import request_finished, request_started
from django.db import close_old_connections
from django.urls import reverse
from hypothesis import settings

from config.wsgi import application

schema = schemathesis.openapi.from_wsgi(reverse('schema'), application)


@pytest.fixture(autouse=True)
def keep_the_test_connection():
    """What Django's test client does around each request.

    Every request starts and ends closing a connection outside autocommit; in a test
    that connection holds the test's transaction, so closing it breaks every query.
    """
    request_started.disconnect(close_old_connections)
    request_finished.disconnect(close_old_connections)
    yield
    request_started.connect(close_old_connections)
    request_finished.connect(close_old_connections)


@pytest.mark.django_db
@schema.parametrize()
@settings(max_examples=25, deadline=None)
def test_every_operation_answers_what_it_documents(case):
    case.call_and_validate()
