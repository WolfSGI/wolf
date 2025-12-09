import deform
import jsonschema_colander.types
from sqlmodel import Session
from wolf.abc.identity import User
from wolf.abc.resolvers import Params
from wolf.abc.resolvers.routing import Router
from wolf.form import Form, trigger
from wolf.rendering import html, renderer
from wolf.services.flash import SessionMessages
from wolf.wsgi.app import Application
from models import Document


routes = Router()


document_schema = jsonschema_colander.types.Object.from_json(
    Document.model_json_schema(), config={
        "": {
            "exclude": ("id", "author_id", "folder_id")
        },

    }
)


@routes.register('/folders/{folder_id}/new', name="document_create")
class CreateDocument(Form):

    def get_schema(self, request, *, context=None):
        schema = document_schema()
        schema['text'].widget = deform.widget.TextAreaWidget()
        return schema

    @trigger('add', 'Add new document')
    def add(self, request, data, *, context):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)

        sqlsession = request.get(Session)
        params = request.get(Params)
        user = request.get(User)
        sqlsession.add(
            Document(
                author_id=user.id,
                folder_id=params['folder_id'],
                **appstruct
            )
        )
        flash = request.get(SessionMessages)
        flash.add('Folder created.', type="info")
        return request.response_cls.redirect(request.application_uri)


@routes.register(
    '/folders/{folder_id}/browse/{document_id}', name="document_view")
@html
@renderer(template='views/document')
def document_view(request):
    application = request.get(Application)
    sqlsession = request.get(Session)
    params = request.get(Params)
    document = sqlsession.get(Document, params['document_id'])
    return {
        "document": document,
        'path_for': application.resolver.path_for
    }
