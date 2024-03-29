import ast
from dataclasses import dataclass, field
from typing import Any, NamedTuple
from aioinject import Object
from beartype import beartype
from chameleon.codegen import template
from chameleon.astutil import Symbol
from wolf.resources import JSResource, CSSResource
from wolf.registries import TypedRegistry, Registry
from wolf.http.request import Request
from wolf.templates import Templates, EXPRESSION_TYPES
from wolf.pluggability import Installable


class SlotRegistry(TypedRegistry):
    @beartype
    class Types(NamedTuple):
        request: type[Request] = Request
        view: type = Any
        context: type = Any


class SubSlotRegistry(TypedRegistry):
    @beartype
    class Types(NamedTuple):
        request: type[Request] = Request
        manager: type = Any
        view: type = Any
        context: type = Any


class LayoutRegistry(TypedRegistry):
    @beartype
    class Types(NamedTuple):
        request: type[Request] = Request
        view: type = Any
        context: type = Any


def query_slot(econtext, name):
    """Compute the result of a slot expression"""
    request = econtext.get("request")  # mandatory.
    context = econtext.get("context", object())
    view = econtext.get("view", object())
    ui = econtext.get("ui", request.context.resolve(UI))

    try:
        manager = ui.slots.fetch(request, view, context, name=name)
        if manager.__evaluate__(request, view, context):
            return None

        if manager.__metadata__.isclass:
            manager = manager()

        subslots = [
            subslot
            for subslot in ui.subslots.match_grouped(
                request, manager, view, context
            ).values()
            if not subslot.__evaluate__(request, manager, view, context)
        ]
        return manager(request, view, context, items=subslots)

    except LookupError:
        # No slot found. We don't render anything.
        return None


class SlotExpr:
    """
    This is the interpreter of a slot: expression
    """

    def __init__(self, expression):
        self.expression = expression

    def __call__(self, target, engine):
        slot_name = self.expression.strip()
        value = template(
            "query_slot(econtext, name)",
            query_slot=Symbol(query_slot),  # ast of query_slot
            name=ast.Str(s=slot_name),  # our name parameter to query_slot
            mode="eval",
        )
        return [ast.Assign(targets=[target], value=value)]


@dataclass(kw_only=True, slots=True)
class UI(Installable):
    __provides__ = ["UI"]

    slots: Registry = field(default_factory=SlotRegistry)
    subslots: Registry = field(default_factory=SubSlotRegistry)
    layouts: Registry = field(default_factory=LayoutRegistry)
    templates: Templates = field(default_factory=Templates)
    macros: Templates = field(default_factory=Templates)
    resources: set[JSResource | CSSResource] = field(default_factory=set)

    def install(self, application):
        application.services.register(Object(self, type_=UI))
        if "slot" not in EXPRESSION_TYPES:
            EXPRESSION_TYPES["slot"] = SlotExpr

    def __or__(self, other: "UI"):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(
            slots=self.slots | other.slots,
            layouts=self.layouts | other.layouts,
            templates=self.templates | other.templates,
            macros=self.macros | other.macros,
            resources=self.resources | other.resources,
        )
