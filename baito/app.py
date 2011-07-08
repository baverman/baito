from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import ClosingIterator
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple

class App(object):
    def __init__(self):
        self.url_map = Map()
        self.Request = Request
        self.Response = Response

    def expose(self, rule, **kwargs):
        def decorator(func):
            kwargs['endpoint'] = func
            self.url_map.add(Rule(rule, **kwargs))
            return func

        return decorator

    def __call__(self, environ, start_response):
        request = self.Request(environ)
        adapter = self.url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            response = endpoint(request, **values)
            if isinstance(response, basestring):
                response = self.Response(response)
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response), [])

    def run(self, host='localhost', port=8000, use_reloader=True, **kwargs):
        run_simple(host, port, self, use_reloader=use_reloader, **kwargs)