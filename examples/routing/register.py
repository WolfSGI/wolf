import colander
import deform
from models import Person
from wolf.form import Form, trigger
from wolf.abc.resolvers.routing import Router
from wolf.services.flash import SessionMessages
from wolf.wsgi.request import Request
from sqlalchemy.sql import exists
from sqlmodel import Session


routes = Router()


def UniqueEmail(node, value):
    request: Request = node.bindings['request']
    sqlsession = request.get(Session)
    if sqlsession.query(exists().where(Person.email == value)).scalar():
        raise colander.Invalid(node, "Email already in use.")


class RegistrationSchema(colander.Schema):

    name = colander.SchemaNode(
        colander.String(),
        title="Name",
        missing=None
    )

    email = colander.SchemaNode(
        colander.String(),
        title="Email",
        validator=colander.All(colander.Email(), UniqueEmail),
        missing=colander.required
    )

    age = colander.SchemaNode(
        colander.Integer(),
        title="Age",
        missing=colander.required,
        validator=colander.Range(
            min=18,
            min_err="You need to be at least 18 years old")
    )

    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5),
        missing=colander.required,
        widget=deform.widget.CheckedPasswordWidget(redisplay=True),
        description="Type your password and confirm it",
    )


@routes.register('/register')
class Register(Form):

    def get_schema(self, request, *, context):
        return RegistrationSchema()

    @trigger('login', 'Login')
    def save(self, request, data, *, context):
        form = self.get_form(request, context=context)
        appstruct = form.validate(data)

        sqlsession = request.get(Session)
        sqlsession.add(Person(**appstruct))

        flash = request.get(SessionMessages)
        flash.add('Account created.', type="info")
        return request.response_cls.redirect(request.application_uri)
