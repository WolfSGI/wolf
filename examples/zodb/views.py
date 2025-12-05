from kettu.traject import ViewRegistry
from wolf.rendering import html, renderer
from resources import somejs
import models


views = ViewRegistry()


@views.register(models.Folder, '/', name="view")
@html
@renderer(template="views/folder")
def folder_index(request, *, context: object):
    return {
        "folder": context
    }


@views.register(models.Document, '/', name="view")
@html(resources=[somejs])
@renderer
def doc_index(request, *, context: object):
    return f"This is document {context.name}"


@views.register(object, '/fail', name="view")
def failure(request, *, context: object):
    raise RuntimeError("I am so failing")

@views.register(object, '/fail2', name="view")
def failure2(request, *, context: object):
    return request.response_cls(400)
