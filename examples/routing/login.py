import colander
import deform
from wolf.form import Form, trigger
from wolf.identity import Authenticator
from wolf.routing import Router
from wolf.services.flash import SessionMessages


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

    def get_schema(self, request, *, context=None):
        return LoginSchema()

    @trigger('login', 'Login')
    def save(self, request, data, *, context):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)
        authenticator = request.get(Authenticator)
        user = authenticator.from_credentials(request, appstruct)

        flash = request.get(SessionMessages)
        if user is not None:
            authenticator.remember(request, user)
            flash.add('Logged in.', type="success")
            return request.response_cls.redirect(request.application_uri)

        # Login failed.
        flash.add('Login failed.', type="danger")
        return form.render()


@routes.register('/logout')
def logout(request):
    authenticator = request.get(Authenticator)
    authenticator.forget(request)
    flash = request.get(SessionMessages)
    flash.add('Logged out.', type="warning")
    return request.response_cls.redirect(request.application_uri)
