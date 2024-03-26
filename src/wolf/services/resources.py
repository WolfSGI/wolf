import os
import base64
import hashlib
from typing import Sequence
from pathlib import PurePosixPath, Path
from pkg_resources import resource_filename
from mimetypes import guess_type
from autoroutes import Routes
from aioinject import Object, Scoped
from wolf.wsgi.response import WSGIResponse, FileWrapperResponse
from wolf.resources import Resource, known_extensions, NeededResources
from wolf.pluggability import Installable


def generate_sri(filepath: Path):
    hashed = hashlib.sha256()
    with filepath.open('rb') as f:
        while True:
            data = f.read(1024*32)
            if not data:
                break
            hashed.update(data)
    hashed = hashed.digest()
    hash_base64 = base64.b64encode(hashed).decode('utf-8')
    return 'sha256-{}'.format(hash_base64)


class BaseLibrary:
    name: str
    base_path: Path

    def __init__(self, name: str, base_path: str | Path):
        resource = Path(base_path)
        if not resource.exists():
            raise OSError(f'{resource} does not exist.')
        if not resource.is_dir():
            raise TypeError('Library base path must be a directory.')
        if not base_path.is_absolute():
            raise ValueError('Base path needs to be absolute.')
        self.name = name
        self.base_path = base_path

    def __iter__(self):
        pass


class DiscoveryLibrary(BaseLibrary):
    name: str
    base_path: Path

    def __init__(self, name: str, base_path: str | Path, restrict=('*',)):
        super().__init__(name, base_path)
        self.restrictions = restrict

    def __iter__(self):
        for matcher in self.restrictions:
            for path in self.base_path.rglob(matcher):
                yield self.name / path.relative_to(self.base_path), path


class Library(DiscoveryLibrary):

    _resources: set
    _by_name: dict[str, Resource]

    def __init__(self, name: str, base_path: str | Path, restrict=('*',)):
        self._resources = set()
        self._by_name = {}
        super().__init__(name, base_path, restrict=restrict)

    def bind(self, path: str | PurePosixPath, *,
             name: str | None = None,
             bottom: bool = False,
             dependencies: Sequence[Resource] | None = None):
        fullpath = self.base_path / path
        if not fullpath.is_file():
            raise TypeError(f'{path} is not a file.')

        if not fullpath.suffix:
            raise NameError('Filename needs an extension.')

        ext = fullpath.suffix[1:]
        cls = known_extensions.get(ext)
        if not cls:
            raise TypeError('Unknown extension.')

        integrity = generate_sri(fullpath)
        if dependencies is not None:
            dependencies = tuple(dependencies)
        resource = cls(
            f"/{self.name}/{path}",
            bottom=bottom,
            integrity=integrity,
            dependencies=dependencies
        )
        self._resources.add(resource)
        if name:
            self._by_name[name] = resource
        return resource


class StaticAccessor:
    path: str
    resources: Routes | None
    libraries: dict[str, Library]

    def __init__(self, path: str):
        self.path = path
        self.resources = None
        self.libraries = dict()

    def finalize(self):
        self.resources = Routes()
        for name, library in self.libraries.items():
            for uri, full_path in iter(library):
                stats = os.stat(full_path)
                content_type, encoding = guess_type(full_path)
                if not content_type:
                    content_type = 'octet/steam'
                elif content_type.startswith("text/") or \
                        content_type == "application/javascript":
                    content_type += "; charset=utf-8"
                info = {
                    "filepath": full_path,
                    "size": stats.st_size,
                    "content_type": content_type
                }
                self.resources.add(str('/' / PurePosixPath(uri)), **info)

    def add_library(self, library: Library, override: bool = False):
        if library.name in self.libraries and not override:
            raise KeyError(f"Library {library.name!r} already exists.")
        self.libraries[library.name] = library

    def add_static(self, name: str,
                   base_path: str | Path, restrict=('*',),
                   override: bool = False) -> Library:
        library = DiscoveryLibrary(name, base_path, restrict=restrict)
        self.add_library(library, override=override)
        return library

    def add_package_static(self,
                           package_static: str,
                           restrict=('*',),
                           override: bool = False
                           ):
        # package_static of form:  package_name:path
        pkg, resource_name = package_static.split(":")
        resource = Path(resource_filename(pkg, resource_name))
        return self.add_static(
            package_static, resource, restrict=restrict, override=override)


class ResourceManager(Installable, StaticAccessor):

    def install(self, application):
        application.mounts[self.path] = self
        application.services.register(Object(self, type_=ResourceManager))
        application.services.register(Scoped(self.needed_resources))

    def needed_resources(self) -> NeededResources:
        return NeededResources(self.path)

    def resolve(self, environ):
        match, _ = self.resources.match(environ['PATH_INFO'])
        if not match:
            return WSGIResponse(status=404)

        headers = {
            "Content-Length": str(match["size"]),
            "Content-Type": match["content_type"]
        }
        if environ['REQUEST_METHOD'] == "HEAD":
            return WSGIResponse(200, headers=headers)

        if 'wsgi.file_wrapper' not in environ:
            return WSGIResponse.from_file_path(
                match["filepath"],
                headers=headers
            )
        return FileWrapperResponse(match["filepath"], headers=headers)
