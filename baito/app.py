from routes.mapper import Mapper
from webob import Request, Response
from webob.exc import HTTPException, HTTPNotFound
from wsgiref.simple_server import make_server

class App(object):
    def __init__(self):
        self.url_map = Mapper()
        self.Request = Request
        self.Response = Response

    def expose(self, rule, **kwargs):
        def decorator(func):
            kwargs['endpoint'] = func
            self.url_map.connect(None, rule, **kwargs)
            return func

        return decorator

    def __call__(self, environ, start_response):
        request = self.Request(environ)
        try:
            result = self.url_map.match(None, environ)
            if not result:
                raise HTTPNotFound()

            endpoint = result.pop('endpoint')
            response = endpoint(request, **result)
            if isinstance(response, basestring):
                response = self.Response(response)
        except HTTPException, e:
            response = e

        return response(environ, start_response)

    def run(self, host='localhost', port=8000):
        httpd = make_server(host, port, self)
        httpd.serve_forever()