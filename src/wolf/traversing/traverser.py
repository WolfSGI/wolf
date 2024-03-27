import typing as t
from wrapt import ObjectProxy
from pathlib import PurePosixPath
from inspect import signature, _empty as empty, isclass
from wolf.http.request import Request
from wolf.typed.datastructures import TypedSet
from wolf.typed.router import TypedRouter


C = t.TypeVar("C")
Factory = t.Callable[[Request, t.Any, t.Mapping[str, t.Any]], C]


class Traversed(ObjectProxy):
    __parent__: t.Any
    __path__: str

    def __init__(self, wrapped, *, parent: t.Any, path: str):
        super().__init__(wrapped)
        self.__parent__ = parent
        if type(parent) is Traversed:
            self.__path__ = f"{parent.__path__}/{path}"
        else:
            self.__path__ = path


def paths(path: str) -> t.Tuple[str, str]:
    root = PurePosixPath(path)
    parents = list(root.parents)
    yield str(root), ""
    for parent in parents[:-1]:
        yield str(parent), "/" + str(root.relative_to(parent))


class Node:

    def __init__(self, cls, path):
        self.cls = cls
        self.path = path

    def __hash__(self):
        return hash(self.cls)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.cls == other.cls and self.path == other.path
        elif isclass(other):
            return other == self.cls
        raise TypeError(
            f"Cannot establish equality between {self!r} and {other!r}")

    def __repr__(self):
        return f"{self.cls} -> {self.path}"


class ViewRegistry(TypedRouter):
    pass


class Traverser(TypedRouter):
    __slots__ = ("_reverse",)

    def __init__(self):
        self._reverse: TypedSet[t.Any, Node] = TypedSet()
        super().__init__()

    def add(
            self,
            root: t.Type[t.Any],
            path: str,
            method,
            factory: Factory,
            **kwargs
    ) -> None:
        sig = signature(factory)
        if sig.return_annotation is empty:
            raise TypeError("Factories need to specify a return type.")
        self[root].add(path, method, factory, **kwargs)
        self._reverse.add(sig.return_annotation, Node(root, path))

    def traverse(
        self,
        root: t.Any,
        path: str,
        method: str,
        request: Request,
        partial: bool = None,
    ) -> t.Tuple[t.Any, str]:
        for stub, branch in paths(path):
            for matcher in self.lookup(root.__class__):
                found = matcher.get(stub, method)
                if found:
                    obj = found.routed(request, root, **found.params)
                    if obj is None:
                        raise LookupError(stub)
                    traversed = Traversed(obj, parent=root, path=stub)
                    if not branch:
                        return traversed, ""
                    return self.traverse(
                        traversed, branch, method, request, partial=partial
                    )
        if partial:
            return root, path
        raise LookupError()

    def reverse(self, node1, node2):
        path_list = [[node1]]
        path_index = 0

        # To keep track of previously visited nodes
        previous_nodes = {node1}
        if node1 == node2:
            return path_list[0]

        while path_index < len(path_list):
            current_path = path_list[path_index]
            last_node = current_path[-1]
            next_nodes = self._reverse[last_node]

            # Search goal node
            for candidate in next_nodes:
                if candidate == node2:
                    current_path.append(candidate)
                    resolved = "/"
                    for node in reversed(current_path[1:]):
                        resolved += node.path
                    return resolved

            # Add new paths
            for next_node in next_nodes:
                if next_node not in previous_nodes:
                    new_path = current_path[:]
                    new_path.append(next_node)
                    path_list.append(new_path)
                    # To avoid backtracking
                    previous_nodes.add(next_node)
            # Continue to next path in list
            path_index += 1
        # No path is found
        raise LookupError("No path found.")

    def __or__(self, other: "Traverser"):
        new: Traverser = super().__or__(other)
        new._reverse = self._reverse | other._reverse
        return new

    def __ior__(self, other: "Traverser"):
        new: Traverser = super().__ior__(other)
        new._reverse |= other._reverse
        return new
