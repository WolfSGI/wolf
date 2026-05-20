from unittest.mock import Mock
from wolf.app.services.flash import Flash, Message


class FakeSession(dict[str]):

    def __init__(self, *args, **kwargs):
        self.save = Mock()
        super().__init__(*args, **kwargs)


def test_flash_service():
    session = FakeSession()
    flash = Flash()
    messages = flash.session_messages(session)

    messages.add('test')
    session.save.assert_called_once()
    session.save.reset_mock()

    assert list(messages) == [Message(body='test', type='info')]
    session.save.assert_called_once()
    session.save.reset_mock()

    assert list(messages) == []
    session.save.assert_not_called()
