import pathlib
import http_session_file
from http_session import Session
from sleigh.asgi.app import Application
from sleigh.middlewares.session import HTTPSessions
from sleigh.http.datastructures import Cookies
from sleigh.rendering import json, html, renderer
from sleigh.ui import UI
from sleigh.templates import Templates
from aioinject import Object


ui = UI(
    templates=Templates('templates')
)


app = Application(
    middlewares=[
        HTTPSessions(
            store=http_session_file.FileStore(
                pathlib.Path('sessions'), 3000
            ),
            secret="secret",
            salt="salt",
            cookie_name="cookie_name",
            secure=False,
            TTL=3000
        ).async_http_session
    ]
)

app.services.register(Object(ui))


@app.router.register('/')
@html
@renderer(template='views/index')
async def my_handler(request):
    return {"value": 1}


@app.router.register('/json')
@json
async def my_handler(request):
    return {"test": 1}


@app.router.register('/html')
@html
async def my_page(request):
    return """<html>
<body>
<script>ws = new WebSocket('ws://localhost:8000/ws_echo');
ws.addEventListener("message",(msg) => console.log(msg.data));
ws.addEventListener("open", () => {
  ws.send("hi");
});
</script>
</body>
</html>
"""

@app.router.register('/ws_echo', methods=['WS'])
async def my_ws(request, ws):
    async for msg in ws.iter_messages():
        print(msg)


app.finalize()
