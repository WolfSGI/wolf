import pytest
from wolf.json import JSONSchema, JSONValidationError
from jsonschema_rs import ValidationError


address_schema = {
    "$id": "https://example.com/address.schema.json",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "description": "An address similar to http://microformats.org/wiki/h-card",
    "type": "object",
    "properties": {
        "postOfficeBox": {
            "type": "string"
        },
        "extendedAddress": {
            "type": "string"
        },
        "streetAddress": {
            "type": "string"
        },
        "locality": {
            "type": "string"
        },
        "region": {
            "type": "string"
    },
        "postalCode": {
            "type": "string"
        },
        "countryName": {
            "type": "string"
        }
    },
    "required": [ "locality", "region", "countryName" ],
    "dependentRequired": {
        "postOfficeBox": [ "streetAddress" ],
        "extendedAddress": [ "streetAddress" ]
    }
}


def test_jsonschema_base():
    schema = JSONSchema(address_schema)
    schema == address_schema

    assert schema.validate({
        "postOfficeBox": "123",
        "streetAddress": "456 Main St",
        "locality": "Cityville",
        "region": "State",
        "postalCode": "12345",
        "countryName": "Country"
    }) is None


def test_jsonschema_validation_errors():
    schema = JSONSchema(address_schema)

    with pytest.raises(JSONValidationError) as exc:
        schema.validate({
            "postOfficeBox": 123,
            "streetAddress": 456,
            "locality": "Cityville",
            "region": "State",
            "postalCode": "12345",
            "countryName": "Country"
        })

    errors = exc.value.errors
    assert len(errors) == 2
    assert isinstance(errors[0], ValidationError)
    assert errors[0].message == '123 is not of type "string"'
    assert errors[1].message == '456 is not of type "string"'
