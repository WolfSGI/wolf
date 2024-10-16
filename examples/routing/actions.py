from typing import Any, NamedTuple
from prejudice.errors import ConstraintError
from wolf.wsgi.request import WSGIRequest
from kettu.identity import User, anonymous
from kettu.registries import TypedRegistry


class Actions(TypedRegistry):

    class Types(NamedTuple):
        request: type[WSGIRequest] = WSGIRequest
        view: type = Any
        context: type = Any


actions = Actions()


def is_not_anonymous(request, view, context):
    if request.get(User) is anonymous:
        raise ConstraintError('User is anonymous.')


def is_anonymous(request, view, context):
    if request.get(User) is not anonymous:
        raise ConstraintError('User is not anonymous.')


@actions.register(
    ..., name='login', title='Login', description='Login action',
    conditions=(is_anonymous,))
def login_action(request, view, item):
    return '/login'


@actions.register(
    ..., name='register', title='Register', description='Registration',
    conditions=(is_anonymous,))
def register_action(request, view, item):
    return '/register'


@actions.register(
    ..., name='logout', title='Logout', description='Logout action',
    conditions=(is_not_anonymous,))
def logout_action(request, view, item):
    return '/logout'
