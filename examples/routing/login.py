import colander
import deform
from winkel.routing import Router
from winkel.services.flash import SessionMessages
from winkel.form import Form, trigger
from winkel import Response, Authenticator


routes = Router()


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


@routes.register('/login')
class Login(Form):

    def get_schema(self, scope, *, context=None):
        return LoginSchema()

    @trigger('login', 'Login')
    def save(self, scope, data, *, context):
        form = self.get_form(scope, context=context)
        appstruct = form.validate(data)
        authenticator = scope.get(Authenticator)
        user = authenticator.from_credentials(scope, appstruct)

        flash = scope.get(SessionMessages)
        if user is not None:
            authenticator.remember(scope, user)
            flash.add('Logged in.', type="success")
            return Response.redirect(scope.environ.application_uri)

        # Login failed.
        flash.add('Login failed.', type="danger")
        return form.render()


@routes.register('/logout')
def logout(scope):
    authenticator = scope.get(Authenticator)
    authenticator.forget(scope)
    flash = scope.get(SessionMessages)
    flash.add('Logged out.', type="warning")
    return Response.redirect(scope.environ.application_uri)
