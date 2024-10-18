from kettu.http.app import Application
from kettu.http.headers import Query
from kettu.identity import User
from wolf.rendering import html, json, renderer
from kettu.routing import Router
from wolf.decorators import ondemand
from wolf.services.post import Mailman
from wolf.wsgi.response import WSGIResponse
from wolf.wsgi.request import WSGIRequest
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description
from wolf.services.flash import SessionMessages
from rq import Queue


class request_content_type(BaseMatcher):

    def __init__(self, *values: str):
        self.values: tuple[str] = tuple(values)

    def describe_to(self, description: Description):
        description.append_text(
            'String matching a wilcards string '
        ).append_text(self.value)

    def _matches(self, request):
        return request.accept.negotiate(self.values)


routes = Router()


@routes.register('/')
@html
@renderer(template='views/index')
def index(request):
    application = request.get(Application)
    return {
        'user': request.get(User),
        'path_for': application.router.path_for
    }


@routes.register('/test/job')
@ondemand
def task_queue(request: WSGIRequest, queue: Queue, flash: SessionMessages):
    queue.enqueue(print, 'this was queued')
    flash.add('Job was enqueued.', type="info")
    return WSGIResponse.redirect(request.application_uri)


@routes.register('/test/ondemand')
@html
@ondemand
def ondemand(root: Application):
    return f"{root.__class__.__name__}"


@routes.register('/test/bare')
@html
@renderer
def bare(request):
    return "This is my bare view"


@routes.register('/test/json')
@json
def json_view(request):
    return {"key": "value"}


@routes.register(
    '/test/negotiate',
    requirements={"request": request_content_type('application/json')})
@json
def test_json_negotiation(request):
    return {"key": "value"}


@routes.register(
    '/test/negotiate',
    priority=1,
    requirements={"request": request_content_type('text/html')})
@html
def test_html_negotiation(request):
    return "key : value"


def some_pipe(handler):
    def some_filter(request):
        query = request.get(Query)
        if query.get('die'):
            return request.response_cls(200, body='ouch, I died')
        return handler(request)
    return some_filter


@routes.register('/test/filtered', pipeline=(some_pipe,))
@html
@renderer
def filtered(request):
    return "This is my filtered view"


@routes.register('/test/error')
def test2(request):
    raise NotImplementedError("Damn")


@routes.register('/test/mailer')
@html
def mail(request):
    mailman = request.get(Mailman)
    mailman.post(
         'test@test.com', ['toto@test.com'], 'Test', 'A text.'
    )
    return 'I sent an email.'
