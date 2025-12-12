from typing import Any
from collections import deque
from wolf.abc.resolvers import Located
from wolf.app.render import renderer
from wolf.app.request import Request
from wolf.app.services.flash import SessionMessages
from wolf.rendering.ui import SlotRegistry, LayoutRegistry, SubSlotRegistry


slots = SlotRegistry()
layouts = LayoutRegistry()
subslots = SubSlotRegistry()


@layouts.register(..., name="")
@renderer(template='layout', layout_name=None)
def default_layout(
        request: Request, view: Any, context: Any, name: str, content: str):
    return {'content': content, 'view': view, 'context': context}


@slots.register(..., name='above_content')
class AboveContent:

    @renderer(template='slots/above', layout_name=None)
    def __call__(
            self, request: Request, view: Any, context: Any, *, items):
        return {
            'items': [item(request, self, view, context) for item in items]
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
        request: Request, manager: AboveContent, view: Any, context: Any):
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
