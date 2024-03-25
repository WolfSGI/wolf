import http_session_file
import pathlib
import vernacular
import logging.config
from wolf.ui import UI
from wolf.routing import Application
from wolf.templates import Templates
from wolf.middlewares import HTTPSession, NoAnonymous
from wolf.resources import JSResource, CSSResource
# from wolf.services.resources import ResourceManager
# from wolf.services import (
#     Transactional, HTTPSessions, Flash, SessionAuthenticator,
#     SQLDatabase, TranslationService, PostOffice
# )


import register, login, views, actions, ui, folder, document, db


app = Application(middlewares=[
    HTTPSessions(
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
