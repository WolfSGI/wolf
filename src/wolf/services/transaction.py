import logging
from typing import Callable
from contextlib import contextmanager
from transaction import TransactionManager
from winkel.response import Response
from winkel.plugins import ServiceManager, Configuration, factory


logger = logging.getLogger(__name__)


class Transactional(ServiceManager, Configuration):
    manager: Callable[[], TransactionManager] = TransactionManager

    @factory('scoped')
    def transaction_factory(self, context) -> TransactionManager:
        return context.stack.enter_context(self.transactional(context))

    @contextmanager
    def transactional(self, context):
        manager = self.manager()
        with manager as txn:
            yield manager
            response = context.get(Response)
            if txn.isDoomed() or response.status >= 400:
                txn.abort()
