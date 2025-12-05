import http_session_file
import pathlib
import logging.config
import structlog
from kettu.resources import CSSResource, JSResource
from wolf.wsgi.app import PublishingApplication
from wolf.middlewares import HTTPSession
from wolf.services.flash import Flash
from wolf.services.resources import ResourceManager
from wolf.templates import Templates
from wolf.ui import UI
from wolf.wsgi.publisher import PublicationRoot
import ui, views, resources, middleware, models
from ZODB.FileStorage import FileStorage
from ZODB import Connection, DB



here = pathlib.Path(__file__).parent.resolve()


libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_library(resources.static)
libraries.add_library(resources.my_super_lib)
libraries.add_library(resources.my_lib)
libraries.finalize()


app = PublishingApplication(
    views=views.views,
    middlewares=[
        middleware.Transaction(),
        HTTPSession(
            store=http_session_file.FileStore(
                pathlib.Path('sessions'), 3000
            ),
            secret="secret",
            salt="salt",
            cookie_name="cookie_name",
            secure=False,
            TTL=3000
        )
    ]
)

app.use(
    middleware.ZODB(db=DB(FileStorage("example.fs"))),
    libraries,
    Flash(),
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
    )
)

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


def zodb_root(svcs_container):
    connection = svcs_container.get(Connection)
    root = connection.root()
    if not "app" in root:
        app = models.ApplicationRoot()
        folder = app["folder"] = models.Folder()
        folder["doc1"] = models.Document(
            name="whatever",
            content="This is document 1"
        )
        root['app'] = app
    return root['app']


app.services.register_factory(PublicationRoot, zodb_root)


app.finalize()
wsgi_app = app
