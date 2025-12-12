import jsonschema_rs
from frozendict import frozendict
from functools import cached_property


class JSONSchema(frozendict):

    @cached_property
    def validator(self):
        return jsonschema_rs.validator_for(self)

    def validate(self, instance):
        yield from self.validator.iter_errors(instance)
