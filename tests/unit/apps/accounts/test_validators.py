import re
from collections.abc import Callable

import phonenumbers
from django.core.exceptions import ValidationError
from hypothesis import given
from hypothesis import strategies as st

from apps.accounts.constants import (
    PERSON_NAME_LENGTH,
    PERSON_NAME_PATTERN,
    USERNAME_PATTERN,
)
from apps.accounts.validators import (
    country_names,
    validate_person_name,
    validate_phone,
    validate_username,
)

# conventions/data.md §3: a Peruvian cellphone.
PERU_CELLPHONE_PATTERN = r'^\+519[0-9]{8}$'


def accepts(validator: Callable[[str], None], value: str) -> bool:
    try:
        validator(value)
    except ValidationError:
        return False
    return True


@given(st.from_regex(USERNAME_PATTERN, fullmatch=True) | st.text(max_size=40))
def test_a_username_is_accepted_only_when_it_follows_its_format(value):
    follows_format = re.fullmatch(USERNAME_PATTERN, value) is not None

    assert accepts(validate_username, value) == follows_format


@given(st.from_regex(PERSON_NAME_PATTERN, fullmatch=True) | st.text(max_size=300))
def test_a_person_name_is_accepted_only_when_it_follows_its_format(value):
    shortest, longest = PERSON_NAME_LENGTH
    follows_format = shortest <= len(value) <= longest and (
        re.fullmatch(PERSON_NAME_PATTERN, value) is not None
    )

    assert accepts(validate_person_name, value) == follows_format


@given(st.from_regex(PERU_CELLPHONE_PATTERN, fullmatch=True))
def test_every_peruvian_cellphone_is_accepted(value):
    assert accepts(validate_phone, value)


def test_every_region_with_its_own_numbering_has_its_spanish_name():
    names = country_names()

    without_name = {
        region for region in phonenumbers.SUPPORTED_REGIONS if not names.get(region)
    }
    assert without_name == set()
