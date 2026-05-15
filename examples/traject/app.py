import pathlib
import http_session_file
from wolf.app import Application
from wolf.app.middlewares import HTTPSession
from wolf.app.resolvers import TrajectResolver
from wolf.app.services.flash import Flash
from wolf.app.services.post import PostOffice
from wolf.app.services.resources import ResourceManager
from wolf.rendering.resources import CSSResource, JSResource
from wolf.rendering.templates import Templates
from wolf.rendering.ui import UI
from wolf_jwt import JWTService
from wolf_sql import SQLDatabase

import ui, views, store, factories, resources  # noqa


here = pathlib.Path(__file__).parent.resolve()


libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_library(resources.static)
libraries.add_library(resources.my_super_lib)
libraries.add_library(resources.my_lib)


app = Application(
    resolver=TrajectResolver(
        contexts=factories.registry,
        views=views.registry
    ),
    middlewares=[
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

app.services.register_value(store.Stores, store.stores)


app.use(
    libraries,
    JWTService(
        private_key=here / 'identities' / 'jwt.priv',
        public_key=here / 'identities' / 'jwt.pub'
    ),
    PostOffice(
        path=pathlib.Path('test.mail')
    ),
    SQLDatabase.from_url(url="sqlite:///database.db"),
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
    )
)
