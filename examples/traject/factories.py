from sqlmodel import Session as SQLSession, select
from wolf.wsgi.app import Application
from wolf.wsgi.request import Request
from kettu.exceptions import HTTPError
from wolf.abc.resolvers import Extra
from wolf.abc.resolvers.traject import ContextRegistry
from models import Folder, Document


registry = ContextRegistry()


@registry.register(Application, '/folders/{folder_id}')
def folder_factory(
        request: Request, parent: Application,  *,
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
