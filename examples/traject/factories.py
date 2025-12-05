from sqlmodel import Session as SQLSession, select
from wolf.wsgi.app import WSGIApplication
from kettu.http.request import Request
from kettu.http.exceptions import HTTPError
from kettu.routing import Extra
from kettu.traject import ContextRegistry
from models import Folder, Document


registry = ContextRegistry()


@registry.register(WSGIApplication, '/folders/{folder_id}')
def folder_factory(
        request: Request, parent: WSGIApplication,  *,
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
