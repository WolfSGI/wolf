from pathlib import Path, PosixPath
from wolf.app.render.html import BoundResources
from html_resources.library import Library


HERE = Path(__file__).parent.resolve()
RESOURCES = HERE / "resources"

STUPID_LAYOUT = """
<html>
  <head>
  </head>
  <body>
    <h1>My site</h1>
  </body>
</html>
"""


def test_bound_apply():
    store = Library.from_discovery("my_lib", RESOURCES)
    js_resource = store.bind('hello.js')
    css_resource = store.bind('example.css',
                              dependencies=[js_resource])

    bound = BoundResources("static")
    bound.add(css_resource)
    body = bound.apply(STUPID_LAYOUT)
    assert body == b"""
<html>
  <head>
  <script src="static/my_lib/hello.js" integrity="sha256-yFZn6wscZfgJynmR6A9NFVN6HMNUwHhfE1TrMnJ2HPA="></script>
<link rel="stylesheet" href="static/my_lib/example.css" integrity="sha256-ogCX0ULq8M9SOMyenKNy8HjkPNfr9lNokjg7i09IUBs=" />
</head>
  <body>
    <h1>My site</h1>
  </body>
</html>
"""

    body = bound.apply(STUPID_LAYOUT, base_uri="http://whatever/")
    assert body == b"""
<html>
  <head>
  <script src="http:/whatever/static/my_lib/hello.js" integrity="sha256-yFZn6wscZfgJynmR6A9NFVN6HMNUwHhfE1TrMnJ2HPA="></script>
<link rel="stylesheet" href="http:/whatever/static/my_lib/example.css" integrity="sha256-ogCX0ULq8M9SOMyenKNy8HjkPNfr9lNokjg7i09IUBs=" />
</head>
  <body>
    <h1>My site</h1>
  </body>
</html>
"""
