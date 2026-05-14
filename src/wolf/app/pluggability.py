import structlog
from fct_annotate import annotation


logger = structlog.get_logger("wolf.app.pluggability")


@annotation("install_method")
class install_method:
    _for: type | tuple[type]


class Installable:

    def install(self, application):
        """Default method for `Installable`. All methods decorated by the
        `install_method` decorator will be called on the application object.
        """
        for restrict, func in install_method.find(self):
            if not isinstance(application, restrict):
                logger.warning(
                    f"Trying to install on {self} but method {func} "
                    f"requires an application of type {restrict}"
                )
                pass
            else:
                logger.debug(f"Installation calls {self} on {application}.")
                func(application)
