"""JSON utilities
"""
from functools import cached_property

import jsonschema_rs
from frozendict import frozendict


class JSONValidationError(Exception):
    """Errors collection from schema validation.
    """

    def __init__(self, errors: tuple[jsonschema_rs.ValidationError, ...]):
        self.errors = errors


class JSONSchema(frozendict):
    """JSONSchema wrapper as a immutable mapping.
    Validation capabilities based on jsonschema_rs.
    """

    @cached_property
    def validator(self):
        """Returns a validator for the current schema.
        """
        return jsonschema_rs.validator_for(self)

    def validate(self, instance) -> None:
        """Validate a JSON value against the schema.
        """
        errors = tuple(self.validator.iter_errors(instance))
        if errors:
            raise JSONValidationError(errors)
