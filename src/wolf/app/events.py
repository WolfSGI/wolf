from typing import NamedTuple
from blinker import NamedSignal, Namespace


class Lifecycle(NamedTuple):
    on_init: NamedSignal
    on_request: NamedSignal
    on_response: NamedSignal
    on_error: NamedSignal

    @classmethod
    def from_namespace(cls, namespace: Namespace):
        return cls(
            on_init=namespace.signal('initialize'),
            on_request=namespace.signal('on_request'),
            on_response=namespace.signal('on_response'),
            on_error=namespace.signal('on_error')
        )


class Events(Namespace):
    lifecycle: Lifecycle

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lifecycle = Lifecycle.from_namespace(self)
