import jsonschema_colander.types
from sqlmodel import Session
from wolf.abc.identity import User
from wolf.abc.resolvers import Params
from wolf.abc.resolvers.routing import Router
from wolf.form import Form, trigger
from wolf.app.render import html, renderer
from wolf.app.services.flash import SessionMessages
from wolf.app import Application
from models import Folder


routes = Router()


folder_schema = jsonschema_colander.types.Object.from_json(
    Folder.model_json_schema(), config={
        "": {
            "exclude": ("id", "author_id")
        },
    }
)


@routes.register('/folders/new', name="folder_create")
class CreateFolder(Form):

    def get_schema(self, request, *, context=None):
        return folder_schema()

    @trigger('add', 'Add new folder')
    def add(self, request, data, *, context):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)
        sqlsession = request.get(Session)
        user = request.get(User)
        sqlsession.add(Folder(author_id=user.id, **appstruct))

        flash = request.get(SessionMessages)
        flash.add('Folder created.', type="info")
        return request.response_cls.redirect(request.application_uri)


@routes.register('/folders/{folder_id}', name="folder_view")
@html
@renderer(template='views/folder')
def folder_view(request):
    application = request.get(Application)
    sqlsession = request.get(Session)
    params = request.get(Params)
    folder = sqlsession.get(Folder, params['folder_id'])
    return {
        "folder": folder,
        'path_for': application.resolver.path_for
    }
