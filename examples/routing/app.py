import http_session_file
import pathlib
import vernacular
from aioinject import Object
import logging.config
from wolf.ui import UI
from wolf.wsgi.app import RoutingApplication
from wolf.templates import Templates
from wolf.middlewares import HTTPSession, NoAnonymous
from wolf.resources import JSResource, CSSResource
from wolf.services.resources import ResourceManager
from wolf.services.auth import SessionAuthenticator
from wolf.services.flash import Flash
from wolf.services.sqldb import SQLDatabase

import register, login, views, actions, ui, folder, document, db


here = pathlib.Path(__file__).parent.resolve()

libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_static('example', here / 'static', restrict=('*.jpg',))
libraries.finalize()


app = RoutingApplication(middlewares=[
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
])

app.use(
    libraries,
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

app.router |= (
    register.routes |
    login.routes |
    views.routes |
    folder.routes |
    document.routes
)
app.services.register(Object(actions.actions))

# Run once at startup:
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        'wolf': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
})

app.finalize()

wsgi_app = app
