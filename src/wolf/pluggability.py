import logging
from wolf.annotations import annotation


logger = logging.getLogger(__name__)


class install_method(annotation):
    name = '__install_method__'

    def __init__(self, _for: type | tuple[type]):
        self.annotation = _for


class Installable:

    def install(self, application):
        for restrict, func in install_method.find(self):
            if not isinstance(application, restrict):
                logger.warning(
                    f'Trying to install on {self} but method {func} '
                    f'requires an application of type {restrict}'
                )
                pass
            else:
                func(application)
