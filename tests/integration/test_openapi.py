"""The generated OpenAPI schema documents every operation completely.

It reads the schema as a black box (rules/reference/api-docs.md): no database, no
requests. What each API answers is checked by its integration tests and Schemathesis.
"""

from typing import Any

import pytest
from drf_spectacular.generators import SchemaGenerator
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

ENVELOPE_KEYS = {'success', 'message', 'data', 'detail'}
SCHEMA_URI = 'urn:openapi'


def as_json_schema(node: Any) -> Any:
    """OpenAPI 3.0 to JSON Schema: `nullable` becomes a null option, refs absolute."""
    if isinstance(node, list):
        return [as_json_schema(item) for item in node]
    if not isinstance(node, dict):
        return node
    converted = {key: as_json_schema(value) for key, value in node.items()}
    if isinstance(converted.get('$ref'), str):
        converted['$ref'] = SCHEMA_URI + converted['$ref']
    if converted.pop('nullable', False):
        return {'anyOf': [converted, {'type': 'null'}]}
    return converted


SCHEMA = SchemaGenerator().get_schema(request=None, public=True)
REGISTRY = Registry().with_resource(
    SCHEMA_URI, DRAFT202012.create_resource(as_json_schema(SCHEMA))
)
OPERATIONS = {
    f'{method.upper()} {path}': operation
    for path, path_item in SCHEMA['paths'].items()
    for method, operation in path_item.items()
}


def component(schema: dict[str, Any]) -> dict[str, Any]:
    name = schema['$ref'].rsplit('/', 1)[-1]
    return SCHEMA['components']['schemas'][name]


def media(operation: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """(where, content) of its request and of each of its responses, in JSON."""
    contents = [('request', operation.get('requestBody', {}).get('content', {}))]
    contents += [
        (code, response.get('content', {}))
        for code, response in operation['responses'].items()
    ]
    return [
        (where, content['application/json'])
        for where, content in contents
        if 'application/json' in content
    ]


def expected_codes(operation: dict[str, Any]) -> set[str]:
    parameters = operation.get('parameters', [])
    takes_input = 'requestBody' in operation or any(
        parameter['in'] == 'query' for parameter in parameters
    )
    conditions = {
        '400': takes_input,
        '401': any(requirement for requirement in operation.get('security', [])),
        '404': any(parameter['in'] == 'path' for parameter in parameters),
    }
    return {'429', '500'} | {code for code, applies in conditions.items() if applies}


operations = pytest.mark.parametrize(
    'operation', OPERATIONS.values(), ids=OPERATIONS.keys()
)


@operations
def test_has_a_summary_and_a_description(operation):
    assert operation.get('summary')
    assert operation.get('description')


@operations
def test_documents_its_success_and_every_code_it_can_always_answer(operation):
    codes = set(operation['responses'])

    assert any(code.startswith('2') for code in codes)
    assert expected_codes(operation) - codes == set()


@operations
def test_every_error_answers_the_error_envelope(operation):
    for code, response in operation['responses'].items():
        if int(code) >= 400:
            schema = response['content']['application/json']['schema']
            assert set(component(schema)['properties']) == ENVELOPE_KEYS, code


@operations
def test_every_error_example_shows_its_code(operation):
    for code, content in media(operation):
        if code != 'request' and int(code) >= 400:
            for name, example in content.get('examples', {}).items():
                assert 'code' in example['value']['detail'], (code, name)


@operations
def test_every_example_matches_its_schema(operation):
    for where, content in media(operation):
        validator = Draft202012Validator(
            as_json_schema(content['schema']), registry=REGISTRY
        )
        for name, example in content.get('examples', {}).items():
            errors = [
                error.message for error in validator.iter_errors(example['value'])
            ]
            assert errors == [], (where, name)
