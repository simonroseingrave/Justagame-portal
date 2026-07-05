"""A tiny WSGI micro-framework: routing, request/response objects, and
static file serving. Pure standard library -- this app has zero third
party dependencies, so it runs anywhere Python 3 runs with no `pip
install` step required.
"""
import re
import os
import mimetypes
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlsplit


class Request:
    def __init__(self, environ):
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = urlsplit(environ.get("PATH_INFO", "/")).path or "/"
        self.query = parse_qs(environ.get("QUERY_STRING", ""))
        self.cookies = SimpleCookie()
        cookie_header = environ.get("HTTP_COOKIE", "")
        if cookie_header:
            self.cookies.load(cookie_header)
        self._form = None

    def get_query(self, name, default=None):
        values = self.query.get(name)
        return values[0] if values else default

    def get_cookie(self, name, default=None):
        if name in self.cookies:
            return self.cookies[name].value
        return default

    @property
    def form(self):
        if self._form is None:
            try:
                length = int(self.environ.get("CONTENT_LENGTH") or 0)
            except ValueError:
                length = 0
            body = self.environ["wsgi.input"].read(length) if length else b""
            self._form = parse_qs(body.decode("utf-8"))
        return self._form

    def form_get(self, name, default=""):
        vals = self.form.get(name)
        return vals[0] if vals else default

    def form_get_list(self, name):
        """Return all submitted values for a field (e.g. multi-select checkboxes)."""
        return self.form.get(name, [])


class Response:
    def __init__(self, body="", status=200, content_type="text/html; charset=utf-8"):
        self.body = body
        self.status = status
        self.headers = [("Content-Type", content_type)]
        self._cookies = SimpleCookie()

    def set_cookie(self, name, value, max_age=None, path="/", httponly=True):
        self._cookies[name] = value
        self._cookies[name]["path"] = path
        if httponly:
            self._cookies[name]["httponly"] = True
        if max_age is not None:
            self._cookies[name]["max-age"] = max_age

    def delete_cookie(self, name, path="/"):
        self.set_cookie(name, "", max_age=0, path=path)

    def render(self, start_response):
        status_line = f"{self.status} {STATUS_TEXT.get(self.status, 'OK')}"
        body_bytes = self.body.encode("utf-8") if isinstance(self.body, str) else self.body
        headers = list(self.headers)
        headers.append(("Content-Length", str(len(body_bytes))))
        for morsel in self._cookies.values():
            headers.append(("Set-Cookie", morsel.OutputString()))
        start_response(status_line, headers)
        return [body_bytes]


STATUS_TEXT = {
    200: "OK", 302: "Found", 303: "See Other", 401: "Unauthorized",
    403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed", 500: "Internal Server Error",
}


def redirect(location, status=303):
    resp = Response(body="", status=status)
    resp.headers.append(("Location", location))
    return resp


class Router:
    def __init__(self):
        self.routes = []  # (method, compiled_regex, handler)

    def add(self, method, pattern, handler):
        def convert(m):
            token = m.group(0)
            if token.startswith("<int:"):
                name = token[len("<int:"):-1]
                return f"(?P<{name}>\\d+)"
            name = token[1:-1]
            return f"(?P<{name}>[^/]+)"

        # Single pass so an already-substituted (?P<name>...) group can
        # never be re-matched and corrupted by a second substitution.
        regex = re.sub(r"<int:\w+>|<\w+>", convert, pattern)
        compiled = re.compile("^" + regex + "$")
        self.routes.append((method.upper(), compiled, handler))

    def get(self, pattern):
        def deco(fn):
            self.add("GET", pattern, fn)
            return fn
        return deco

    def post(self, pattern):
        def deco(fn):
            self.add("POST", pattern, fn)
            return fn
        return deco

    def match(self, method, path):
        allowed = set()
        for m, regex, handler in self.routes:
            mobj = regex.match(path)
            if mobj:
                if m == method:
                    return handler, mobj.groupdict(), None
                allowed.add(m)
        if allowed:
            return None, None, "405"
        return None, None, "404"


class App:
    def __init__(self, router, static_dir, static_url="/static/"):
        self.router = router
        self.static_dir = static_dir
        self.static_url = static_url

    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            if req.path.startswith(self.static_url):
                resp = self.serve_static(req.path)
            else:
                handler, params, error = self.router.match(req.method, req.path)
                if error == "404":
                    resp = Response("404 Not Found", status=404)
                elif error == "405":
                    resp = Response("405 Method Not Allowed", status=405)
                else:
                    resp = handler(req, **(params or {}))
        except Exception as exc:  # pragma: no cover - defensive fallback
            import traceback
            traceback.print_exc()
            resp = Response(f"<pre>500 Internal Server Error\n{exc}</pre>", status=500)
        return resp.render(start_response)

    def serve_static(self, path):
        rel = path[len(self.static_url):]
        full_path = os.path.normpath(os.path.join(self.static_dir, rel))
        if not full_path.startswith(os.path.normpath(self.static_dir)):
            return Response("403 Forbidden", status=403)
        if not os.path.isfile(full_path):
            return Response("404 Not Found", status=404)
        content_type, _ = mimetypes.guess_type(full_path)
        with open(full_path, "rb") as fh:
            data = fh.read()
        resp = Response(body=data, content_type=content_type or "application/octet-stream")
        return resp
