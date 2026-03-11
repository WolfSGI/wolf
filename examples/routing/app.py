import pathlib
import structlog
import logging.config
import vernacular
import http_session_file
from redis import Redis
from rq import Queue
from wolf.rendering.ui import UI
from wolf.rendering.resources import JSResource, CSSResource
from wolf.rendering.templates import Templates
from wolf.app import Application
from wolf.app.auth.sources.openid import KeycloakSource
from wolf.app.middlewares import HTTPSession, NoAnonymous
from wolf.app.resolvers import RouteResolver
from wolf.app.services.auth import SessionAuthenticator
from wolf.app.services.flash import Flash
from wolf.app.services.post import PostOffice
from wolf.app.services.resources import ResourceManager
from wolf.app.services.sqldb import SQLDatabase
from wolf.app.services.translation import TranslationService
from keycloak import KeycloakOpenIDConnection

import register, login, views, actions, ui, folder, document, db  # noqa


keycloak_connection = KeycloakOpenIDConnection(
    server_url="http://localhost:9090",
    realm_name="novareto.de",
    client_id="novareto_de",
    client_secret_key="JcVTUM6IGK4CR51yw4Qg1K6WL1XAeblt",
    verify=False,  # BBB attention
)

keycloak_source = KeycloakSource(
    keycloak_connection,
    title="Keycloak source",
    description="Keycloak users on the novareto.de realm"
)


here = pathlib.Path(__file__).parent.resolve()

libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_static('example', here / 'static', restrict=('*.jpg', '*.ico'))
libraries.finalize()


vernacular.COMPILE = True
i18Catalog = vernacular.Translations()
for translation in vernacular.translations(pathlib.Path('translations')):
    i18Catalog.add(translation)


app = Application(
    resolver=RouteResolver(),
    middlewares=(
        HTTPSession(
            store=http_session_file.FileStore(
                pathlib.Path('sessions'), 3000
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
        path=pathlib.Path('test.mail')
    ),
    TranslationService(
        translations=i18Catalog,
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
    SQLDatabase(
        url="sqlite:///database.db"
    ),
    SessionAuthenticator(
        sources={
            "sql": db.DBSource(),
            "keycloak": keycloak_source
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


# Run once at startup:
def extract_from_record(_, __, event_dict):
    """
    Extract thread and process names and add them to the event dict.
    """
    record = event_dict["_record"]
    event_dict["thread_name"] = record.threadName
    event_dict["process_name"] = record.processName
    return event_dict


timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    # Add extra attributes of LogRecord objects to the event dictionary
    # so that values passed in the extra parameter of log methods pass
    # through to log output.
    structlog.stdlib.ExtraAdder(),
    timestamper,
]

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        "plain": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=False),
            ],
            "foreign_pre_chain": pre_chain,
        },
        "colored": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                extract_from_record,
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            "foreign_pre_chain": pre_chain,
        },
    },
    'handlers': {
        "default": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "colored",
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'wolf': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
})


app.finalize()

wsgi_app = app
