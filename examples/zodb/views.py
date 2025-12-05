from kettu.traversing import ViewRegistry
from wolf.rendering import html, renderer
from resources import somejs
import models


views = ViewRegistry()


@views.register(models.Folder, '/', name="view")
@html(resources=[somejs])
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
