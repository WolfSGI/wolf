import deform
import jsonschema_colander.types
from sqlmodel import Session
from winkel.form import Form, trigger
from winkel.routing import Application, Router, Params
from winkel.services.flash import SessionMessages
from winkel import User, Response, html, renderer
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

    def get_schema(self, scope, *, context=None):
        schema = document_schema()
        schema['text'].widget = deform.widget.TextAreaWidget()
        return schema

    @trigger('add', 'Add new document')
    def add(self, scope, data, *, context):
        form = self.get_form(scope, context=context)
        appstruct = form.validate(data)

        sqlsession = scope.get(Session)
        params = scope.get(Params)
        user = scope.get(User)
        sqlsession.add(
            Document(
                author_id=user.id,
                folder_id=params['folder_id'],
                **appstruct
            )
        )
        flash = scope.get(SessionMessages)
        flash.add('Folder created.', type="info")
        return Response.redirect(scope.environ.application_uri)


@routes.register(
    '/folders/{folder_id}/browse/{document_id}', name="document_view")
@html
@renderer(template='views/document')
def document_view(scope):
    application = scope.get(Application)
    sqlsession = scope.get(Session)
    params = scope.get(Params)
    document = sqlsession.get(Document, params['document_id'])
    return {
        "document": document,
        'path_for': application.router.path_for
    }
