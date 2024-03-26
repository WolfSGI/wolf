# this whole module will be moved to a dedicated  package
# as it has heavy dependencies, like deform/colander.

import deform
import colander
from abc import ABC, abstractmethod
from wolf.annotations import annotation
from wolf.http.datastructures import Data
from wolf.http.exceptions import HTTPError
from wolf.rendering import html, renderer
from wolf.resources import NeededResources
from wolf.routing import APIView


class trigger(annotation):
    name = "__form_trigger__"

    def __init__(self, name: str, title: str, order: int = 0):
        self.annotation = {"name": name, "title": title, "order": order}


class Form(ABC, APIView):
    def __init__(self):
        triggers = sorted(
            tuple(trigger.find(self)), key=lambda x: (x[0]["order"], x[0]["name"])
        )
        self.triggers = {(ann["name"], "__trigger__"): func for ann, func in triggers}
        self.buttons = [
            deform.form.Button(
                value="__trigger__", name=ann["name"], title=ann["title"]
            )
            for ann, func in triggers
        ]

    def get_initial_data(self, request, *, context=None):
        return {}

    @abstractmethod
    def get_schema(self, request, *, context=None) -> colander.Schema:
        pass

    def get_form(self, request, *, context=None) -> deform.form.Form:
        schema = self.get_schema(request, context=context).bind(
            request=request, context=context
        )
        form = deform.form.Form(schema, buttons=self.buttons)
        initial_data = self.get_initial_data(request, context=context)
        if initial_data:
            appstruct = schema.deserialize(initial_data)
            form.set_appstruct(appstruct)
        self.include_resources(request, form)
        return form

    def include_resources(self, request, form):
        needed = request.get(NeededResources, default=None)
        if needed is not None:
            for rtype, resources in form.get_widget_resources().items():
                for resource in resources:
                    needed.add_resource(resource, rtype)

    @html
    @renderer
    def GET(self, request, *, context=None):
        form = self.get_form(request, context=context)
        return form.render()

    @html
    @renderer
    def POST(self, request, *, context=None):
        data = request.get(Data)
        for trigger in self.triggers:
            if trigger in data.form:
                action = self.triggers[trigger]
                try:
                    return action(request, data.form, context=context)
                except deform.exception.ValidationFailure as e:
                    return e.render()
        raise HTTPError(400)
