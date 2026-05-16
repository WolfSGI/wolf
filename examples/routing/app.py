import pathlib
import vernacular
import http_session_file

import structlog
from redis import Redis
from rq import Queue

from authsources_keycloak.actions import Challenge, Fetch
from authsources_keycloak.source import KeycloakSource
from keycloak import KeycloakOpenIDConnection
from wolf.app import Application
from wolf.app.middlewares import HTTPSession, NoAnonymous
from wolf.app.resolvers import RouteResolver
from wolf.app.services.auth import SessionAuthenticator
from wolf.app.services.flash import Flash
from wolf.app.services.post import PostOffice
from wolf.app.services.resources import ResourceManager
from wolf.app.services.translation import TranslationService
from wolf.rendering.resources import JSResource, CSSResource
from wolf.rendering.templates import Templates
from wolf.rendering.ui import UI
from wolf_sql import SQLDatabase

import register, login, views, actions, ui, folder, document, db, models  # noqa


logger = structlog.get_logger("example.routing")


# keycloak_connection = KeycloakOpenIDConnection(
#     server_url="http://localhost:9090",
#     realm_name="novareto.de",
#     client_id="novareto_de",
#     client_secret_key="JcVTUM6IGK4CR51yw4Qg1K6WL1XAeblt",
#     verify=False,  # BBB attention
# )

# keycloak_source = KeycloakSource(
#     keycloak_connection,
#     title="Keycloak source",
#     description="Keycloak users on the novareto.de realm",
#     actions=(Challenge, Fetch)
# )

# COMPILE PO FILES
vernacular.COMPILE = True

# HELPER
HERE = pathlib.Path(__file__).parent.resolve()


#### CONFIG OF THE APP
database_source = db.DBSource(
    title="SQL source",
    description="SQL users",
    actions=(db.Login, db.Fetch),
    usertype=models.Person
)


libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_static('example', HERE / 'static', restrict=('*.jpg', '*.ico'))

app = Application(
    resolver=RouteResolver(),
    middlewares=(
        HTTPSession(
            store=http_session_file.FileStore(
                HERE / 'sessions', 3000
            ),
            secret="secret",
            salt="salt",
            cookie_name="cookie_name",
            secure=False,
            TTL=3000
        ),
        NoAnonymous(
            login_url='/login',
            allowed_urls={'/register', '/test'}
        )
    )
)

app.use(
    libraries,
    PostOffice(
        path=HERE / 'test.mail'
    ),
    TranslationService.from_paths(
        paths=[HERE / 'translations'],
        default_domain="routing",
        accepted_languages=["fr", "en", "de"]
    ),
    UI(
        slots=ui.slots,
        subslots=ui.subslots,
        layouts=ui.layouts,
        templates=Templates('templates'),
        resources={
            CSSResource(
                "/bootstrap@5.0.2/dist/css/bootstrap.min.css",
                root="https://cdn.jsdelivr.net/npm",
                integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC",  # noqa
                crossorigin="anonymous"
            ),
            CSSResource(
                "/bootstrap-icons@1.11.1/font/bootstrap-icons.css",
                root="https://cdn.jsdelivr.net/npm",
                integrity="sha384-4LISF5TTJX/fLmGSxO53rV4miRxdg84mZsxmO8Rx5jGtp/LbrixFETvWa5a6sESd",  # noqa
                crossorigin="anonymous"
            ),
            JSResource(
                "/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js",
                root="https://cdn.jsdelivr.net/npm",
                bottom=True,
                integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM",  # noqa
                crossorigin="anonymous"
            ),
            JSResource(
                "/jquery-3.7.1.min.js",
                root="https://code.jquery.com",
                integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo=",  # noqa
                crossorigin="anonymous"
            )
        }
    ),
    SQLDatabase(url="sqlite:///database.db", echo=True),
    SessionAuthenticator(
        sources={
            "sql": database_source,
            #"keycloak": keycloak_source
        },
        user_key="user"
    ),
    Flash()
)

app.resolver.router |= (
    register.routes |
    login.routes |
    views.routes |
    folder.routes |
    document.routes
)
app.services.register_value(actions.Actions, actions.actions)


# Jobs queue
q = Queue(connection=Redis())
app.services.register_value(Queue, q)

app.events.lifecycle.on_init.send(
    'startup',
    config={"example": "Config on startup"}
)

#### Example of lifecycle events
@app.events.lifecycle.on_request.connect
def echo_request(app, *, request):
    logger.info(f"Request created: {request}")


@app.events.lifecycle.on_response.connect
def echo_response(app, *, response):
    logger.info(f"Response returned: {response}")
