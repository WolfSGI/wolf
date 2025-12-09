import colander
import deform
import jsonschema_colander.types
from hamcrest import equal_to
from sqlmodel import Session as SQLSession, select

from wolf import matchers
from wolf.app import Application
from wolf.abc.resolvers import URIResolver
from wolf.abc.resolvers.traject import ViewRegistry
from wolf.form import Form, trigger
from wolf.app.render import html, renderer
from wolf.decorators import ondemand
from models import Folder, Document
from store import Stores, SchemaKey
from resources import somejs


registry = ViewRegistry()


@registry.register(Application, '/', name="view")
@html(resources=[somejs])
@renderer(template='views/index')
def root_index(request, *, context: Application):
    sqlsession = request.get(SQLSession)
    query = select(Folder)
    folders = sqlsession.exec(query).all()
    resolver = request.get(URIResolver)
    return {
        'context': context,
        'folders': folders,
        'path_for': resolver.path_for
    }


@registry.register(Folder, '/', name="view")
@html
@renderer(template='views/folder')
@ondemand
def folder_index(resolver: URIResolver, sqlsession: SQLSession, *, context: Folder):
    query = select(Document).filter(Document.folder_id == context.id)
    documents = sqlsession.exec(query).all()
    return {
        'context': context,
        'documents': documents,
        'path_for': resolver.path_for
    }


@registry.register(Application, '/create_folder', name='create_folder')
class CreateFolder(Form):

    def get_schema(self, request, *, context=None):
        return Folder.get_schema(exclude=("id",))

    @trigger('save', 'Create new folder')
    def save(self, request, data, *, context: Application):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)
        sqlsession = request.get(SQLSession)
        sqlsession.add(
            Folder(
                **appstruct
            )
        )
        return request.response_cls.redirect(request.application_uri)


@colander.deferred
def deferred_choices_widget(node, kw):
    request = kw.get("request")
    stores = request.get(Stores)
    choices = []
    for key, schema in stores['reha'].items():
        choices.append((SchemaKey("reha", *key), schema['description']))
    return deform.widget.SelectWidget(values=choices)


@registry.register(Folder, '/create_document', name='create_document')
class CreateDocument(Form):

    def get_schema(self, request, *, context=None):
        schema = Document.get_schema(
            exclude=("id", "folder_id", "content")
        )
        schema['type'].widget = deferred_choices_widget
        return schema

    @trigger('save', 'Create new document')
    def save(self, request, data, *, context):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)
        sqlsession = request.get(SQLSession)
        sqlsession.add(
            Document(
                **appstruct,
                folder_id=context.id
            )
        )
        return request.response_cls.redirect(request.application_uri)


@registry.register(Document, '/edit', name="edit")
class EditDocument(Form):

    def get_schema(self, request, *, context=None):
        stores = request.get(Stores)
        key = SchemaKey.from_string(context.type)
        schema = stores[key.store].get((key.schema, key.version))
        return jsonschema_colander.types.Object.from_json(schema)()

    def get_initial_data(self, request, *, context=None):
        return context.content

    @trigger('save', 'Update document')
    def save(self, request, data, *, context):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)
        context.content = appstruct
        resolver = path_for(request, context)
        return request.response_cls.redirect(resolver(context, 'view'))


@registry.register(
    Document, '/', name="view",
    requirements={"type": matchers.match_wildcards('schema2.1.2*')})
@html
@renderer
def schema2_document_index(request, *, context: Document):
    return f"I use a schema2: {context.type}"


@registry.register(
    Document, '/', name="view",
    requirements={"type": equal_to('schema1.1.0@reha')})
@html
@renderer
def schema1_document_index(request, context: Document):
    return f"I use a schema1: {context.type}"
