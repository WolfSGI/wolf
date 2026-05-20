import uuid
import pytest
from unittest.mock import Mock, patch
from http_session.meta import Store


class SessionMemoryStore(Store):

    def __init__(self, TTL=None):
        self.data = {}
        self.touch = Mock()
        self.TTL = TTL

    def __iter__(self):
        return iter(self.data.keys())

    def get(self, sid):
        """We return a copy, to avoid mutability by reference.
        """
        data = self.data.get(sid)
        if data is not None:
            return deepcopy(data)
        return data

    def set(self, sid, session):
        self.data[sid] = session

    def clear(self, sid):
        if sid in self.data:
            self.data[sid].clear()

    def delete(self, sid):
        del self.data[sid]


@pytest.fixture
def http_session_store():

    def uuid_generator(count=0):
        while True:
            yield uuid.UUID(int=count)
            count += 1

    def mock_uuid(generator):
        def uuid_patch():
            return next(generator)
        return uuid_patch

    with patch('uuid.uuid4', mock_uuid(uuid_generator())):
        yield SessionMemoryStore
