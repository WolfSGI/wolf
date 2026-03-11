from typing import Any
from wolf.rendering.ui import SlotRegistry, LayoutRegistry, SubSlotRegistry
from wolf.app.render import renderer
from wolf.app.decorators import ondemand
from wolf.app.request import Request
from wolf.app.services.flash import SessionMessages
from wolf.abc.identity import User, anonymous
from actions import Actions
from login import Login


slots = SlotRegistry()
layouts = LayoutRegistry()
subslots = SubSlotRegistry()


@layouts.register(..., name="")
@renderer(template='layout', layout_name=None)
def default_layout(
        request: Request,
        view: Any,
        context: Any,
        name: str,
        content: str):
    return {'content': content, 'view': view, 'context': context}


@slots.register(..., name='actions')
@renderer(template='slots/actions', layout_name=None)
def actions(request: Request, view: Any, context: Any, *, items):
    registry = request.get(Actions)
    matching = registry.match_grouped(request, view, context)
    evaluated = []
    for name, action in matching.items():
        if not action.__evaluate__(request, view, context):
            result = action(request, view, context)
            evaluated.append((action.__metadata__, result))
    return {
        "actions": evaluated,
        'view': view,
        'context': context,
        'manager': actions
    }


@slots.register(..., name='above_content')
class AboveContent:

    @renderer(template='slots/above', layout_name=None)
    def __call__(self,
                 request: Request,
                 view: Any,
                 context: Any,
                 *,
                 items):
        return {
            'items': [item(request, self, view, context) for item in items],
            'view': view, 'context': context, 'manager': self
        }


@subslots.register({"manager": AboveContent}, name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(
        request: Request, manager: AboveContent, view: Any, context: Any):
    flash = request.get(SessionMessages)
    return {
        'messages': list(flash),
        'view': view,
        'context': context,
        'manager': manager
    }


@subslots.register({"manager": AboveContent}, name='identity')
@ondemand
def identity(who_am_i: User):
    if who_am_i is anonymous:
        return ("<div class='container alert alert-secondary'>"
                "Not logged in.</div>")
    return ("<div class='container alert alert-info'>"
            f"You are logged in as {who_am_i.id}</div>")


@slots.register({"view": Login}, name='sneaky')
def sneaky(request: Request,
           view: Login,
           context: Any,
           *,
           items) -> str:
    return "I show up only on the Login page."
