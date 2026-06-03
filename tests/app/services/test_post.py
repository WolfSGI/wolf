from collections import deque
from wolf.app.services.post import Mailman
from email.mime.multipart import MIMEMultipart


def test_mailman_base():
    mailman = Mailman()
    assert isinstance(mailman, deque)
    assert len(mailman) == 0


def test_mailman_message():
    mailman = Mailman()
    msg = mailman.create_message(
        origin='test@test.com',
        targets=['toto@test.com'],
        subject="My subject",
        text="This is some test"
    )
    assert isinstance(msg, MIMEMultipart)
    assert msg["From"] == 'test@test.com'
    assert msg["To"] == "toto@test.com"
    assert msg["Subject"] == "My subject"
    assert msg.get_charset() == "utf-8"
