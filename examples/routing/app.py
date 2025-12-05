import pathlib
import structlog
import logging.config
import vernacular
import http_session_file
from redis import Redis
from rq import Queue
from aioinject import Object
from wolf.ui import UI
from wolf.wsgi.app import WSGIApplication
from wolf.wsgi.resolvers import RouteResolver
from wolf.templates import Templates
from wolf.middlewares import HTTPSession, NoAnonymous
from kettu.resources import JSResource, CSSResource
from wolf.services.resources import ResourceManager
from wolf.services.auth import SessionAuthenticator
from wolf.services.flash import Flash
from wolf.services.sqldb import SQLDatabase
from wolf.services.translation import TranslationService
from wolf.services.post import PostOffice
import register, login, views, actions, ui, folder, document, db


here = pathlib.Path(__file__).parent.resolve()

libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_static('example', here / 'static', restrict=('*.jpg', '*.ico'))
libraries.finalize()


vernacular.COMPILE = True
i18Catalog = vernacular.Translations()
for translation in vernacular.translations(pathlib.Path('translations')):
    i18Catalog.add(translation)


app = WSGIApplication(
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
                integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC",
                crossorigin="anonymous"
            ),
            CSSResource(
                "/bootstrap-icons@1.11.1/font/bootstrap-icons.css",
                root="https://cdn.jsdelivr.net/npm",
                integrity="sha384-4LISF5TTJX/fLmGSxO53rV4miRxdg84mZsxmO8Rx5jGtp/LbrixFETvWa5a6sESd",
                crossorigin="anonymous"
            ),
            JSResource(
                "/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js",
                root="https://cdn.jsdelivr.net/npm",
                bottom=True,
                integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM",
                crossorigin="anonymous"
            ),
            JSResource(
                "/jquery-3.7.1.min.js",
                root="https://code.jquery.com",
                integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo=",
                crossorigin="anonymous"
            )
        }
    ),
    SQLDatabase(
        url="sqlite:///database.db"
    ),
    SessionAuthenticator(
        sources=(db.DBSource(),),
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
