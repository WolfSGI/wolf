from sqlmodel import Session as SQLSession, select
from wolf.http.app import Application
from wolf.http.request import Request
from wolf.routing import Extra
from wolf.traversing import Traverser
from models import Folder, Document


registry = Traverser()


@registry.register(Application, '/folders/{folder_id}')
def folder_factory(
        request: Request, parent: Application,  *,
        folder_id: str) -> Folder:

    sqlsession = request.get(SQLSession)
    folder = sqlsession.get(Folder, folder_id)
    return folder


@registry.register(Folder, '/documents/{document_id}')
def document_factory(
        request: Request, parent: Folder, *,
        document_id: str) -> Document:

    sqlsession = request.get(SQLSession)
    query = select(Document).where(
        Document.id == document_id,
        Document.folder_id == parent.id
    )
    document = sqlsession.exec(query).one_or_none()
    extra = request.get(Extra)
    extra["type"] = document.type
    return document
