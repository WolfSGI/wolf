from typing import Any, NamedTuple
from prejudice.errors import ConstraintError
from winkel.scope import Scope
from winkel.auth import User, anonymous
from winkel.registries import TypedRegistry


class Actions(TypedRegistry):
    class Types(NamedTuple):
        scope: type[Scope] = Scope
        view: type = Any
        context: type = Any


actions = Actions()


def is_not_anonymous(scope, view, context):
    if scope.get(User) is anonymous:
        raise ConstraintError('User is anonymous.')


def is_anonymous(scope, view, context):
    if scope.get('user') is not anonymous:
        raise ConstraintError('User is not anonymous.')


@actions.register(
    ..., name='login', title='Login', description='Login action', conditions=(is_anonymous,))
def login_action(scope, view, item):
    return '/login'


@actions.register(
    ..., name='logout', title='Logout', description='Logout action', conditions=(is_not_anonymous,))
def logout_action(scope, view, item):
    return '/logout'
