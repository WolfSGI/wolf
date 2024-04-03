from pydantic import computed_field
from sqlmodel import Field, SQLModel, Relationship
from kettu.identity import User


class Person(User, SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    name: str | None = None
    age: int
    password: str

    folders: list["Folder"] = Relationship(back_populates="author")

    @computed_field
    @property
    def folders_count(self) -> int:
        return len(self.folders)


class Folder(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    author_id: int = Field(foreign_key="person.id")

    documents: list["Document"] = Relationship(back_populates="folder")
    author: Person = Relationship(back_populates="folders")

    @computed_field
    @property
    def document_count(self) -> int:
        return len(self.documents)


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    text: str
    folder_id: int = Field(foreign_key="folder.id")
    author_id: int = Field(foreign_key="person.id")
    folder: Folder = Relationship(back_populates="documents")
