from persistent import Persistent
from persistent.mapping import PersistentMapping


class Document(Persistent):

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


class Folder(PersistentMapping):
    pass


class ApplicationRoot(Folder):
    pass
