from typing import Any
from collections import deque
from wolf.app.request import Request
from wolf.app.render import renderer
from wolf.abc.identity import User, anonymous
from wolf.app.services.flash import SessionMessages
from wolf.rendering.ui import SlotRegistry, LayoutRegistry, SubSlotRegistry
from wolf.decorators import ondemand
from wolf.abc.resolvers import Located
import models


slots = SlotRegistry()
layouts = LayoutRegistry()
subslots = SubSlotRegistry()


def gather_permissions(user: User, context: object) -> models.Permissions:
    node = context
    permissions = models.Permissions()
    while node is not None:
        if type(node) is Located and isinstance(node, models.Folder):
            if user.id in node.editors:
                permissions.add('local editor')
            node = node.__parent__
        else:
            node = None
    return permissions


@layouts.register(..., name="")
@renderer(template='layout', layout_name=None)
def default_layout(
        request: Request, view: Any, context: Any, name: str, content: str):
    return {'content': content, 'view': view, 'context': context}


@slots.register(..., name='above_content')
class AboveContent:

    @renderer(template='slots/above', layout_name=None)
    def __call__(self, request: Request, *, view: Any, context: Any, items):
        return {
            'items': [
                item(request, manager=self, view=view, context=context)
                for item in items
            ]
        }


@subslots.register({"manager": AboveContent}, name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(
        request: Request, manager: AboveContent, view: Any, context: Any):
    flash = request.get(SessionMessages)
    return {
        'messages': list(flash)
    }


@subslots.register({'manager': AboveContent}, name='crumbs')
@renderer(template='slots/breadcrumbs', layout_name=None)
def breadcrumbs(
        request: Request, *, manager: AboveContent, view: Any, context: Any):
    node = context
    parents = deque()
    while node is not None:
        if type(node) is Located:
            parents.appendleft((node.__path__, node))
            node = node.__parent__
        else:
            node = None

    return {
        'crumbs': parents,
        'view': view,
        'context': context,
        'manager': manager
    }

@subslots.register({"manager": AboveContent}, name='identity')
@ondemand
def identity(who_am_i: User, *, context):
    if who_am_i is anonymous:
        return ("<div class='container alert alert-secondary'>"
                "Not logged in.</div>")
    permissions = gather_permissions(who_am_i, context)
    return ("<div class='container alert alert-info'>"
            f"You are logged in as {who_am_i.id} ({', '.join(permissions)})</div>")