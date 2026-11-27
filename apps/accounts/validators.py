import re
from functools import cache
from itertools import groupby
from string import ascii_lowercase, digits
from typing import Any

import phonenumbers
import yaml
from django.core.exceptions import ValidationError
from phonenumbers import (
    COUNTRY_CODE_TO_REGION_CODE,
    NumberParseException,
    PhoneMetadata,
    PhoneNumber,
    PhoneNumberType,
)

from apps.accounts.constants import (
    COUNTRY_NAMES_PATH,
    NAME_INVALID_CHARACTERS,
    NAME_TOO_LONG,
    NAME_TOO_SHORT,
    PASSWORD_LENGTH,
    PASSWORD_LENGTH_INVALID,
    PASSWORD_MAX_REPEATED,
    PASSWORD_MIN_DIFFERENCE,
    PASSWORD_MISSING_DIGIT,
    PASSWORD_MISSING_SPECIAL,
    PASSWORD_REPEATED_CHARACTER,
    PASSWORD_REQUIRED,
    PASSWORD_SIMILAR,
    PASSWORD_WITH_SPACES,
    PERSON_NAME_LENGTH,
    PERSON_NAME_PATTERN,
    PHONE_COUNTRY_INVALID,
    PHONE_DIGITS_ONLY,
    PHONE_INVALID,
    PHONE_INVALID_PREFIX,
    USERNAME_ACCENTED_LETTERS,
    USERNAME_HAS_ACCENTS,
    USERNAME_HAS_SPACES,
    USERNAME_INVALID_CHARACTERS,
    USERNAME_LEADING_LETTERS,
    USERNAME_LEADING_LETTERS_MISSING,
    USERNAME_LENGTH,
    USERNAME_TOO_LONG,
    USERNAME_TOO_SHORT,
)

USERNAME_CHARACTERS = frozenset(ascii_lowercase + digits)
E164_PATTERN = r'\+[0-9]+'
MOBILE_TYPES = (PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE)
# A mobile numbering such as Peru's "9\d{8}": one leading digit, then any digits.
SINGLE_LEADING_DIGIT = r'([0-9])\\d\{[0-9]+\}'


def normalize_person_name(value: str) -> str:
    """Trims, leaves one space between words and lowercases."""
    return ' '.join(value.split()).lower()


def validate_person_name(value: str) -> None:
    """A name already normalized: its length first, then its letters."""
    shortest, longest = PERSON_NAME_LENGTH
    if len(value) < shortest:
        raise ValidationError(NAME_TOO_SHORT)
    if len(value) > longest:
        raise ValidationError(NAME_TOO_LONG)
    if not re.fullmatch(PERSON_NAME_PATTERN, value):
        raise ValidationError(NAME_INVALID_CHARACTERS)


def validate_username(value: str) -> None:
    """Every condition the username breaks, each with its own message."""
    shortest, longest = USERNAME_LENGTH
    if len(value) > longest:
        raise ValidationError(USERNAME_TOO_LONG)
    leading = value[:USERNAME_LEADING_LETTERS]
    conditions = (
        (any(character.isspace() for character in value), USERNAME_HAS_SPACES),
        (any(c in USERNAME_ACCENTED_LETTERS for c in value), USERNAME_HAS_ACCENTS),
        (
            any(_is_foreign(character) for character in value),
            USERNAME_INVALID_CHARACTERS,
        ),
        (
            any(character in digits for character in leading),
            USERNAME_LEADING_LETTERS_MISSING,
        ),
        (
            len(value) < shortest,
            USERNAME_TOO_SHORT.format(missing=shortest - len(value)),
        ),
    )
    errors = [message for broken, message in conditions if broken]
    if errors:
        raise ValidationError(errors)


def validate_phone(value: str) -> None:
    """A cellphone in E.164 that follows its country's numbering."""
    if not re.fullmatch(E164_PATTERN, value):
        raise ValidationError(PHONE_DIGITS_ONLY)
    region = _region_of(value)
    numbering = _mobile_numbering(region)
    if region is None or numbering is None:
        raise ValidationError(PHONE_COUNTRY_INVALID)
    if not _is_mobile(value):
        raise ValidationError(_numbering_hint(region, *numbering))


@cache
def country_names() -> dict[str, str]:
    """The Spanish name of every region with its own numbering, read once."""
    return yaml.safe_load(COUNTRY_NAMES_PATH.read_text(encoding='utf-8'))


def _is_foreign(character: str) -> bool:
    return not (
        character in USERNAME_CHARACTERS
        or character.isspace()
        or character in USERNAME_ACCENTED_LETTERS
    )


def _region_of(value: str) -> str | None:
    """The main country of an E.164 number's code (codes never prefix one another)."""
    digits_after_plus = value[1:]
    if digits_after_plus.startswith('0'):
        return None  # no country code starts with 0
    for size in range(1, 4):
        regions = COUNTRY_CODE_TO_REGION_CODE.get(int(digits_after_plus[:size]))
        if regions:
            return regions[0]
    return None


def _is_mobile(value: str) -> bool:
    try:
        number = phonenumbers.parse(value)
    except NumberParseException:
        return False
    return (
        phonenumbers.is_valid_number(number)
        and phonenumbers.number_type(number) in MOBILE_TYPES
    )


def _mobile_numbering(region: str | None) -> tuple[PhoneNumber, str] | None:
    """An example cellphone of the country and the pattern its cellphones follow."""
    if region is None:
        return None
    example = phonenumbers.example_number_for_type(region, PhoneNumberType.MOBILE)
    metadata = PhoneMetadata.metadata_for_region(region)
    mobile = metadata.mobile if metadata else None
    if example is None or mobile is None or mobile.national_number_pattern is None:
        return None
    return example, mobile.national_number_pattern


def _numbering_hint(region: str, example: PhoneNumber, pattern: str) -> str:
    """What a cellphone of that country looks like, from its example number."""
    leading = re.fullmatch(SINGLE_LEADING_DIGIT, pattern)
    return PHONE_INVALID.format(
        country=country_names()[region],
        digits=len(str(example.national_number)),
        prefix=PHONE_INVALID_PREFIX.format(digit=leading.group(1)) if leading else '',
    )


class PasswordConditionsValidator:
    """R3 and L3: every condition the password misses, each with its message."""

    def validate(self, password: str, user: Any = None) -> None:
        if not password:
            raise ValidationError(PASSWORD_REQUIRED)
        shortest, longest = PASSWORD_LENGTH
        conditions = (
            (not shortest <= len(password) <= longest, PASSWORD_LENGTH_INVALID),
            (
                not any(character in digits for character in password),
                PASSWORD_MISSING_DIGIT,
            ),
            (
                not any(_is_special(character) for character in password),
                PASSWORD_MISSING_SPECIAL,
            ),
            (any(character.isspace() for character in password), PASSWORD_WITH_SPACES),
            (
                _longest_run(password) > PASSWORD_MAX_REPEATED,
                PASSWORD_REPEATED_CHARACTER,
            ),
        )
        errors = [message for missed, message in conditions if missed]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self) -> str:
        return ''


class PasswordSimilarityValidator:
    """R4 and L5: far enough from the username and from each word of the names."""

    def validate(self, password: str, user: Any = None) -> None:
        shortest, longest = PASSWORD_LENGTH
        # A password out of its length already fails; a short one is close to anything.
        if user is None or not shortest <= len(password) <= longest:
            return
        words = [user.username, *user.first_name.split(), *user.last_name.split()]
        lowered = password.lower()
        if any(
            _edit_distance(lowered, word.lower()) < PASSWORD_MIN_DIFFERENCE
            for word in words
            if word
        ):
            raise ValidationError(PASSWORD_SIMILAR)

    def get_help_text(self) -> str:
        return ''


def _is_special(character: str) -> bool:
    return not (character.isalnum() or character.isspace())


def _longest_run(value: str) -> int:
    """The most times one character repeats in a row."""
    return max((len(list(run)) for _, run in groupby(value)), default=0)


def _edit_distance(first: str, second: str) -> int:
    """Levenshtein: the fewest insertions, deletions or substitutions between them."""
    previous = list(range(len(second) + 1))
    for row, first_character in enumerate(first, start=1):
        current = [row]
        for column, second_character in enumerate(second, start=1):
            current.append(
                min(
                    previous[column] + 1,
                    current[column - 1] + 1,
                    previous[column - 1] + (first_character != second_character),
                )
            )
        previous = current
    return previous[-1]
