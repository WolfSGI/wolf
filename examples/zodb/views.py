import colander
import deform
from wolf.abc.resolvers.traject import ViewRegistry
from wolf.app.render import html, renderer
from wolf.form import Form, trigger
from wolf.abc.auth import Authenticator
from wolf.abc.resolvers.routing import Router
from wolf.app.services.flash import SessionMessages

import models
from resources import somejs


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



class LoginSchema(colander.Schema):

    username = colander.SchemaNode(
        colander.String(),
        title="Name"
    )

    password = colander.SchemaNode(
        colander.String(),
        title="password",
        widget=deform.widget.PasswordWidget()
    )


@views.register(models.ApplicationRoot, '/login')
class Login(Form):

    def get_schema(self, request, *, context=None):
        return LoginSchema()

    @trigger('login', 'Login')
    def save(self, request, data, *, context):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)
        authenticator = request.get(Authenticator)
        source_id, user = authenticator.challenge(request, appstruct)

        flash = request.get(SessionMessages)
        if user is not None:
            authenticator.remember(request, source_id, user)
            flash.add('Logged in.', type="success")
            return request.response_cls.redirect(request.application_uri)

        # Login failed.
        flash.add('Login failed.', type="danger")
        return form.render()


@views.register(models.ApplicationRoot, '/logout')
def logout(request):
    authenticator = request.get(Authenticator)
    authenticator.forget(request)
    flash = request.get(SessionMessages)
    flash.add('Logged out.', type="warning")
    return request.response_cls.redirect(request.application_uri)
