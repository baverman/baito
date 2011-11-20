from routes.mapper import Mapper
from routes.util import URLGenerator, GenerationException

from webob import Request, Response
from webob.exc import HTTPException, HTTPNotFound, HTTPFound

from beaker.middleware import SessionMiddleware

from wsgiref.simple_server import make_server
from functools import wraps

class BaitoRequest(Request):
    def __init__(self, app, environ):
        Request.__init__(self, environ)

        self.app = app
        self.url_generator = URLGenerator(app.url_map, environ)
        self.session = environ.get('beaker.session', None)

    def url_for(self, name, value=None, **kwargs):
        module, _, name = name.rpartition(':')
        relative_url = not module
        module = module or self.module
        if module:
            kwargs['module'] = module

        if value is not None:
            route = self.url_generator.mapper._routenames.get(name)
            if route:
                if len(route.reqs) == 1:
                    kwargs[route.reqs.keys()[0]] = value
                else:
                    raise GenerationException('Could not generate URL. You must provide key arguments')
        try:
            return self.url_generator(name, **kwargs)
        except GenerationException:
            if relative_url:
                kwargs['module'] = None
                return self.url_generator(name, **kwargs)
            else:
                raise

    def get_flashed_messages(self):
        return self.session.pop('flash_messages', [])

    def render(self, name, _rtype='default', **kwargs):
        return self.app.render(self, name, _rtype, kwargs)

    def redirect(self, url):
        return HTTPFound(location=url)

    def redirect_for(self, name, value=None, **kwargs):
        return self.redirect(self.url_for(name, value, **kwargs))

    def flash(self, message, category='error'):
        self.session.setdefault('flash_messages', []).append((message, category))


class App(object):
    def __init__(self):
        self.url_map = Mapper()
        self.Request = BaitoRequest
        self.Response = Response

        self.renderers = {}
        self.session_opts = None

        self.on_route_not_found_handler = None

    def expose(self, rule, name=None, **kwargs):
        def decorator(func):
            kwargs['endpoint'] = func
            kwargs['module'] = None
            rname = name or func.__name__
            self.url_map.connect(rname, rule, **kwargs)
            return func

        return decorator

    def __call__(self, environ, start_response):
        request = self.Request(self, environ)
        try:
            result = self.url_map.match(None, environ)
            if not result:
                if self.on_route_not_found_handler:
                    return self.on_route_not_found_handler(environ, start_response)
                else:
                    raise HTTPNotFound()

            endpoint = result.pop('endpoint')
            request.module = result.pop('module', None)
            response = endpoint(request, **result)
            if isinstance(response, basestring):
                response = self.Response(response)
        except HTTPException, e:
            response = e

        if request.session:
            request.session.save()

        return response(environ, start_response)

    def run(self, host='localhost', port=8000):
        httpd = make_server(host, port, self)
        httpd.serve_forever()

    def set_renderer(self, renderer, rtype='default'):
        self.renderers[rtype] = renderer

    def on_route_not_found(self, wsgi_handler):
        self.on_route_not_found_handler = wsgi_handler

    def render(self, request, name, rtype, result, *args, **kwargs):
        result.setdefault('url_for', request.url_for)
        result.setdefault('request', request)
        result.setdefault('get_flashed_messages', request.get_flashed_messages)

        response = self.renderers[rtype](name, result, *args, **kwargs)

        for k, v in result.iteritems():
            if k.startswith('http_'):
                setattr(response, k[5:], v)

        return response

    def renderer(self, name, rtype='default', *args, **kwargs):
        def inner(func):
            @wraps(func)
            def inner2(request, *iargs, **ikwargs):
                result = func(request, *iargs, **ikwargs)
                return self.render(request, name, rtype, result, *args, **kwargs)

            return inner2

        return inner

    @property
    def wsgi_app(self):
        if self.session_opts:
            return SessionMiddleware(self, self.session_opts)
        else:
            return self

    def add_module(self, module):
        module.app = self
        module.propagate_routes(self.url_map)


class Module(object):
    def __init__(self, name):
        self.name = name
        self.app = None

        self.rules = []

    def expose(self, rule, name=None, **kwargs):
        def decorator(func):
            kwargs['endpoint'] = func
            kwargs['module'] = self.name
            rname = name or func.__name__
            self.rules.append((rname, rule, kwargs))
            return func

        return decorator

    def propagate_routes(self, mapper):
        for rname, rule, kwargs in self.rules:
            mapper.connect(rname, rule, **kwargs)