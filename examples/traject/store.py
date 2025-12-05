from typing import NamedTuple


class SchemaKey(NamedTuple):
    store: str
    schema: str
    version: float

    def __str__(self):
        return f"{self.schema}.{self.version}@{self.store}"

    @classmethod
    def from_string(cls, value: str):
        id, store = value.split("@", 1)
        schema, version = id.split(".", 1)
        return cls(store, schema, float(version))


schema1 = {
  "$id": "https://example.com/movie.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "A representation of a movie",
  "type": "object",
  "required": ["title", "director", "releaseDate"],
  "properties": {
    "title": {
      "type": "string"
    },
    "director": {
      "type": "string"
    },
    "releaseDate": {
      "type": "string",
      "format": "date"
    },
    "genre": {
      "type": "string",
      "enum": ["Action", "Comedy", "Drama", "Science Fiction"]
    },
    "duration": {
      "type": "string"
    },
    "cast": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}


schema2 = {
  "$id": "https://example.com/job-posting.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "A representation of a job posting",
  "type": "object",
  "required": ["title", "company", "location", "description"],
  "properties": {
    "title": {
      "type": "string"
    },
    "company": {
      "type": "string"
    },
    "location": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "employmentType": {
      "type": "string"
    },
    "salary": {
      "type": "number",
      "minimum": 0
    },
    "applicationDeadline": {
      "type": "string",
      "format": "date"
    }
  }
}


store: dict[tuple[str, float], dict] = dict()
store[('schema1', 1.0)] = schema1
store[('schema2', 1.2)] = schema2


class Stores(dict[str, dict]):
    pass


stores = Stores(reha=store)
