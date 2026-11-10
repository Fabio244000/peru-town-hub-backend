from django.core.validators import BaseValidator, MaxValueValidator, MinValueValidator


def range_validators(limits: tuple[int, int]) -> list[BaseValidator]:
    """Keep a number between its limits, both included."""
    return [MinValueValidator(limits[0]), MaxValueValidator(limits[1])]
