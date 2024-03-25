import logging
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import Message
from mailbox import Mailbox, Maildir
from functools import cached_property
from pydantic import computed_field
from contextlib import contextmanager
from transaction import TransactionManager
from winkel.response import Response
from winkel.plugins import ServiceManager, Configuration, factory


logger = logging.getLogger(__name__)


class Mailman(list[Message]):

    @staticmethod
    def create_message(origin, targets, subject, text, html=None):
        msg = MIMEMultipart("alternative")
        msg["From"] = origin
        msg["To"] = ','.join(targets)
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


class PostOffice(ServiceManager, Configuration):
    __provides__ = [Mailman]

    path: Path

    @computed_field
    @cached_property
    def mailbox(self) -> Mailbox:
        return Maildir(self.path)

    @factory('scoped')
    def mailer_factory(self, scope) -> Mailman:
        return scope.stack.enter_context(self.mailer(scope))

    @contextmanager
    def mailer(self, scope):
        mailman = Mailman()
        try:
            yield mailman
        except Exception:
            # maybe log.
            raise
        else:
            response = scope.get(Response)
            if response.status >= 400:
                return

            if TransactionManager in scope:
                txn = scope.get(TransactionManager)
                if txn.isDoomed():
                    return

            for message in mailman:
                self.mailbox.add(message)
        finally:
            mailman.clear()
