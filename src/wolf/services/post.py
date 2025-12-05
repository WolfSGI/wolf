import structlog
from dataclasses import dataclass
from pathlib import Path
from contextlib import contextmanager
from collections.abc import Iterator
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import Message
from mailbox import Maildir
from kettu.pluggability import Installable


logger = structlog.get_logger("wolf.services.post")


class Mailman(list[Message]):

    @staticmethod
    def create_message(origin, targets, subject, text, html=None):
        msg = MIMEMultipart("alternative")
        msg["From"] = origin
        msg["To"] = ",".join(targets)
        msg["Subject"] = subject
        msg.set_charset("utf-8")

        part1 = MIMEText(text, "plain")
        part1.set_charset("utf-8")
        msg.attach(part1)

        if html is not None:
            part2 = MIMEText(html, "html")
            part2.set_charset("utf-8")
            msg.attach(part2)

        return msg

    def post(self, *args, **kwargs):
        msg = self.create_message(*args, **kwargs)
        self.append(msg)


@dataclass(kw_only=True)
class PostOffice(Installable):
    path: Path

    def __post_init__(self):
        self.mailbox = Maildir(self.path)

    def install(self, application):
        application.services.register_factory(Mailman, self.mailer)

    @contextmanager
    def mailer(self) -> Iterator[Mailman]:
        mailman = Mailman()
        try:
            yield mailman
        except Exception:
            # maybe log.
            raise
        else:
            for message in mailman:
                self.mailbox.add(message)
        finally:
            mailman.clear()
