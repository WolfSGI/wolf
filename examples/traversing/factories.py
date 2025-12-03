from sqlmodel import Session as SQLSession, select
from wolf.wsgi.app import TraversingApplication
from kettu.http.request import Request
from kettu.http.exceptions import HTTPError
from kettu.routing import Extra
from kettu.traversing import Traverser
from models import Folder, Document


registry = Traverser()


@registry.register(TraversingApplication, '/folders/{folder_id}')
def folder_factory(
        request: Request, parent: TraversingApplication,  *,
        folder_id: str) -> Folder:

    sqlsession = request.get(SQLSession)
    folder: Folder | None = sqlsession.get(Folder, folder_id)
    if folder is None:
        raise HTTPError(404)
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
    if document is None:
        raise HTTPError(404)
    extra = request.get(Extra)
    extra["type"] = document.type
    return document
