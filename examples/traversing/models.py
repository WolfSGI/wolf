import typing as t
import jsonschema_colander.types
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import JSON, Column
from pydantic import computed_field


class Model(SQLModel):

    @classmethod
    def get_schema(cls,
                   exclude: t.Sequence[str] | None = None,
                   include: t.Sequence[str] | None = None):
        return jsonschema_colander.types.Object.from_json(
            cls.model_json_schema(), config={
                "": {
                    "exclude": exclude,
                    "include": include
                },
            }
        )()


class Folder(Model, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    documents: t.List["Document"] = Relationship(back_populates="folder")

    @computed_field
    @property
    def document_count(self) -> int:
        return len(self.documents)


class Document(Model, table=True):

    class Config:
        arbitrary_types_allowed = True

    id: int | None = Field(default=None, primary_key=True)
    title: str
    type: str
    content: dict = Field(default_factory=dict, sa_column=Column(JSON))
    folder_id: int = Field(foreign_key="folder.id")

    folder: Folder = Relationship(back_populates="documents")

    @computed_field
    @property
    def name(self) -> int:
        return self.title
