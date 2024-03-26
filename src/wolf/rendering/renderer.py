import wrapt
import functools
from wolf.ui import UI
from wolf.http.request import Request
from wolf.http.response import Response
from wolf.services.translation import Locale, Translator
from chameleon.zpt.template import PageTemplate


def renderer(wrapped=None, *,
             template: PageTemplate | str | None = None,
             layout_name: str | None = ""):

    @wrapt.decorator
    def rendering_wrapper(wrapped, instance, args, kwargs) -> str | Response:
        content = wrapped(*args, **kwargs)

        if isinstance(content, Response):
            return content

        request: Request = args[0]
        ui = request.context.resolve(UI)
        namespace = {
                'request': request,
                'ui': ui,
                'macros': ui.macros,
                'view': instance or wrapped,
                'context': kwargs.get('context', object()),
            }

        if template is not None:
            if not isinstance(content, dict):
                raise TypeError(
                    'Template defined but no namespace returned.')
            if isinstance(template, str):
                tpl = ui.templates[template]
            else:
                tpl = template

            namespace |= content

            translator: Translator | None = request.get(
                Translator, default=None
            )
            locale: str | None = request.get(
                Locale, default=None
            )
            rendered = tpl.render(
                **namespace,
                translate=translator and translator.translate or None,
                target_language=locale
            )

        elif isinstance(content, str):
            rendered = content
        else:
            raise TypeError(
                f'Unable to render type: {type(content)}.')

        if layout_name is not None:
            view = namespace['view']
            context = namespace['context']
            layout = ui.layouts.fetch(
                request, view, context, name=layout_name
            )
            return layout(
                request, view, context, name=layout_name, content=rendered
            )

        return rendered

    if wrapped is None:
        return functools.partial(
            renderer, template=template, layout_name=layout_name
        )

    return rendering_wrapper(wrapped)
