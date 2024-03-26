from typing import NamedTuple
from pathlib import PurePosixPath
from functools import cache


def multi_urljoin(*parts):
    return "/".join(part.strip("/") for part in parts if part)


class Resource(NamedTuple):
    path: str | PurePosixPath
    root: str | None = None
    bottom: bool = False
    integrity: str | None = None
    crossorigin: str | None = None
    dependencies: tuple["Resource"] | None = None

    def render(self, application_uri) -> bytes:
        pass

    @cache
    def __lineage__(self) -> tuple["Resource"]:
        def unfiltered_lineage():
            if not self.dependencies:
                return
            for dependency in self.dependencies:
                yield from dependency.__lineage__()
                yield dependency

        def filtering():
            seen = set()
            for parent in unfiltered_lineage():
                if parent not in seen:
                    seen.add(parent)
                    yield parent
            if self not in seen:
                yield self
            del seen

        return tuple(filtering())


class JSResource(Resource):
    def render(self, application_uri: str = "") -> bytes:
        url = multi_urljoin(self.root or application_uri, self.path)
        value = f'src="{url}"'
        if self.crossorigin:
            value += f' crossorigin="{self.crossorigin}"'
        if self.integrity:
            value += f' integrity="{self.integrity}"'
        return f"""<script {value}></script>\r\n""".encode()


class CSSResource(Resource):
    def render(self, application_uri: str = "") -> bytes:
        url = multi_urljoin(self.root or application_uri, self.path)
        value = f'href="{url}"'
        if self.crossorigin:
            value += f' crossorigin="{self.crossorigin}"'
        if self.integrity:
            value += f' integrity="{self.integrity}"'
        return f"""<link rel="stylesheet" {value} />\r\n""".encode()


known_extensions = {
    "js": JSResource,
    "css": CSSResource,
}


class NeededResources(set[JSResource | CSSResource]):
    def __init__(self, root: str | PurePosixPath, *args, **kwargs):
        self.root = root
        super().__init__(*args, **kwargs)

    def add_resource(
        self,
        path: str,
        rtype: str,
        *,
        root: str | None = None,
        bottom: bool = False,
        integrity: str | None = None,
        crossorigin: str | None = None,
    ):
        if factory := known_extensions.get(rtype):
            resource = factory(
                path,
                root=root,
                bottom=bottom,
                integrity=integrity,
                crossorigin=crossorigin,
            )
            self.add(resource)
        else:
            raise KeyError(f"Unknown resource type: {rtype}.")

    def unfold(self) -> list[Resource]:
        seen = set()
        final = []
        for resource in self:
            for r in resource.__lineage__():
                if r not in seen:
                    final.append(r)
                    seen.add(r)
        return final

    def apply(self, body: str | bytes, application_uri: str = "") -> bytes:
        if not len(self):
            return body

        if isinstance(body, str):
            body = body.encode()

        top = b""
        bottom = b""
        base_uri = multi_urljoin(application_uri, self.root)
        for resource in self.unfold():
            if resource.bottom:
                bottom += resource.render(base_uri)
            else:
                top += resource.render(base_uri)
        if top:
            body = body.replace(b"</head>", top + b"</head>", 1)
        if bottom:
            body = body.replace(b"</body>", bottom + b"</body>", 1)
        return body
