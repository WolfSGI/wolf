import typing as t
import structlog
from functools import wraps
from dataclasses import dataclass, field
from contextlib import contextmanager
from dataclasses import dataclass
from collections.abc import Iterator
from wolf.pluggability import Installable
from wolf.app.request import Request
from wolf.app.response import Response
from ZODB import DB, Connection
from transaction import Transaction, TransactionManager


logger = structlog.get_logger("wolf.examples.zodb")


@dataclass(kw_only=True)
class Transaction:

    factory: t.Callable[[], TransactionManager] = (
        lambda: TransactionManager(explicit=True)
    )

    def install(self, application):
        application.services.register_factory(
            TransactionManager, self.factory)

    def __call__(self, handler):
        @wraps(handler)
        def middleware(request: Request, *args, **kwargs) -> Response:
            manager = self.factory()
            request.context.register_local_value(TransactionManager, manager)

            txn = manager.begin()
            request.context.register_local_value(Transaction, txn)
            try:
                response = handler(request, *args, **kwargs)
                if txn.isDoomed():
                    logger.info('Transaction aborted: transaction is doomed.')
                    txn.abort()
                elif (isinstance(response, Response)
                      and response.status >= 400):
                    logger.info(f'Transaction aborted: response has code {response.status}')
                    txn.abort()
                else:
                    txn.commit()
                return response
            except Exception:
                txn.abort()
                logger.info('Transaction aborted: an exception occured.')
                raise

        return middleware


@dataclass(kw_only=True)
class ZODB(Installable):

    db: DB

    def install(self, application):
        application.services.register_factory(
            Connection, self.zodb_connection)

    @contextmanager
    def zodb_connection(self, svcs_container) -> Iterator[Connection]:
        transaction_manager = svcs_container.get(TransactionManager)
        conn = self.db.open(transaction_manager)
        try:
            yield conn
        except Exception:
            # maybe log.
            raise
        finally:
            conn.close()
