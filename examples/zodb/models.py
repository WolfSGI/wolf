from collections.abc import Iterable
from persistent import Persistent
from persistent.mapping import PersistentMapping
from BTrees.OOBTree import TreeSet
from wolf.abc.resolvers.consumers import base_consumers, BaseConsumer, NOT_FOUND
from wolf.abc.identity import User, anonymous


class Permissions(set):
    pass


class Document(Persistent):

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


class Folder(PersistentMapping):

    def __init__(self, editors: Iterable[str] = tuple()):
        self.editors = TreeSet()
        if editors:
            for editor in editors:
                self.editors.add(editor)
        super().__init__()


class ApplicationRoot(Folder):
    pass
