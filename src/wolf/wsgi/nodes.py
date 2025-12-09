import sys
import typing as t
from pathlib import PurePosixPath
from abc import ABC, abstractmethod
from collections import UserDict
from kettu.exceptions import HTTPError
from wolf.wsgi.response import Response
from wolf.wsgi.types import (
    WSGICallable, WSGIEnviron, StartResponse, ExceptionInfo
)


class Node(ABC, WSGICallable):

    @abstractmethod
    def resolve(self, environ: WSGIEnviron) -> WSGICallable:
        pass

    def handle_exception(
            self,
            exc_info: ExceptionInfo,
            environ: WSGIEnviron
    ) -> WSGICallable | None:
        """This method handles exceptions happening while the
        application is trying to render/process/interpret the request.
        """
        pass

    def __call__(self, environ: WSGIEnviron, start_response: StartResponse):
        iterable = None
        try:
            iterable = self.resolve(environ)
            yield from iterable(environ, start_response)
        except HTTPError as exc:
            iterable = Response(exc.status, body=exc.body)
            yield from iterable(environ, start_response)
        except Exception:
            iterable = self.handle_exception(sys.exc_info(), environ)
            if iterable is None:
                raise
            yield from iterable(environ, start_response)
        finally:
            if iterable is not None:
                close: t.Callable[[], None] | None = getattr(
                    iterable, "close", None
                )
                if close is not None:
                    try:
                        close()
                    except Exception:
                        self.handle_exception(sys.exc_info(), environ)
                        raise


class Mapping(Node, UserDict[str, WSGICallable]):
    def __setitem__(self, path: str, script: WSGICallable):
        super().__setitem__(str("/" / PurePosixPath(path)), script)

    def resolve(self, environ: WSGIEnviron) -> WSGICallable:
        uri = PurePosixPath(environ["PATH_INFO"])
        for current in (uri, *uri.parents):
            if (script := self.get(str(current))) is not None:
                if current.parents:
                    environ["SCRIPT_NAME"] += str(current)
                if current != uri:
                    environ["PATH_INFO"] = f"/{uri.relative_to(current)}"
                else:
                    environ["PATH_INFO"] = "/"
                return script
        raise HTTPError(404)
