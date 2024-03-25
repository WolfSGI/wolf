from wolf.http.datastructures import Query
from wolf.identity import User
from wolf.rendering import html, json, renderer
from wolf.routing import Router, Application
from wolf.services.post import Mailman


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


@routes.register('/test/bare')
@html
@renderer
def bare(request):
    return "This is my bare view"


@routes.register('/test/json')
@json
def json(request):
    return {"key": "value"}


def some_pipe(handler):
    def some_filter(request):
        query = request.get(Query)
        if query.get('die'):
            return Response(200, body='ouch, I died')
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
