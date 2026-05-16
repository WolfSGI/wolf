from wolf.app.events import Events, Lifecycle
from blinker import NamedSignal, Namespace


def test_events_lifecycle():
    events = Events()
    assert isinstance(events, Namespace)
    assert isinstance(events.lifecycle, Lifecycle)
    assert len(events.lifecycle) == 4

    assert events.signal('initialize') is events.lifecycle.on_init
    assert events.signal('on_request') is events.lifecycle.on_request
    assert events.signal('on_response') is events.lifecycle.on_response
    assert events.signal('on_error') is events.lifecycle.on_error


def test_events_casting():
    ns = Namespace()
    previous_on_init = ns.signal('initialize')

    events = Events(ns)
    assert events.signal('initialize') is previous_on_init
    assert events.lifecycle.on_init is previous_on_init

    new_on_request = ns.signal('on_request')
    assert events.lifecycle.on_request is not new_on_request


def test_events_mapping():
    some_signal = NamedSignal('a signal')
    events = Events({
        'on_error': some_signal
    })
    assert events.lifecycle.on_error is some_signal
