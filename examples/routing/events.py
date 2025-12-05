from uuid import uuid4
from typing import Any, Type
from kettu.registries import Registry, Proxy
from plum import Signature


def event_sorter(result: tuple[Signature, Proxy]):
    return result[1].__metadata__.order


class User:
    pass


class Event:

    def __dispatch__(self):
        return tuple()


class ObjectEvent(Event):

    def __init__(self, obj: Any):
        self.obj = obj

    def __dispatch__(self):
        return (self.obj,)


class UserEvent(ObjectEvent):

    def __init__(self, obj: User):
        self.obj = obj



class Events(Registry):

    def register(self, event_type: Type[Event], *args, name=None, **kwargs):
        event_signature = Signature.from_callable(event_type)
        handler_signature = Signature(*args)
        if not event_signature >= handler_signature:
            raise ValueError(
                'Arguments do not match required event signature')

        if name is None:
            name = str(uuid4())
        return super().register((event_type, *args), name=name, **kwargs)

    def notify(self, event):
        args = event.__dispatch__()
        for handler in self.lookup(event, *args, None, sorter=event_sorter):
            handler(event)


events1 = Events()
events2 = Events()


@events1.register(Event)
def very_simple_handler(event):
    print("Some event occured", event)

@events1.register(ObjectEvent, object, order=2)
def handler_for_all(event):
    print("object was added: ", event.obj)


@events1.register(ObjectEvent, str, order=1)
def handler2_for_str(event):
    print("a string was added: ", event.obj)


@events2.register(ObjectEvent, str, order=0)
def handler3_for_str(event):
    print("FIRST a string was added: ", event.obj)


@events2.register(UserEvent, User, order=0)
def handler_for_user_event(event):
    print("User event", event.obj)


events = events1 | events2


print('------- triggering basic event ------')
events.notify(Event())
print('------- triggering object event 1 ------')
events.notify(ObjectEvent(1))
print('------- triggering object event string ------')
events.notify(ObjectEvent("string"))
print('------- triggering user event user ------')
events.notify(UserEvent(User()))
