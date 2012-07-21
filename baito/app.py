import imp

from routes.mapper import Mapper
from routes.util import URLGenerator, GenerationException

from webob import Request, Response
from webob.exc import HTTPException, HTTPNotFound, HTTPFound

from wsgiref.simple_server import make_server
from functools import wraps

from .utils import get_from_module

def get_full_name(module, name):
    if module:
        return module + '.' + name
    else:
        return name


class BaitoRequest(Request):
    def __init__(self, app, environ):
        Request.__init__(self, environ)

        self.app = app
        self.url_generator = URLGenerator(app.url_map, environ)
        self.session = environ.get('beaker.session', None)

    def url_for(self, name, value=None, **kwargs):
        module, _, name = name.rpartition('.')
        shortname = name
        relative_url = not module

        if kwargs.get('back', False) is True:
            kwargs['back'] = self.path_qs

        if name[0] == '!':
            relative_url = False
            name = name[1:]
        else:
            module = module or self.module
            name = get_full_name(module, name)

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
                return self.url_generator(shortname, **kwargs)
            else:
                raise

    def get_flashed_messages(self):
        return self.session.pop('flash_messages', [])

    def render(self, name, **kwargs):
        return self.app.render(self, name, kwargs)

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

        self._renderer = None

        self.conf = imp.new_module('baito.conf')

    def load_conf(self, path):
        self.conf.__file__ = path
        execfile(path, self.conf.__dict__, self.conf.__dict__)

    def connect(self, name, rule, **kwargs):
        kwargs['_module'] = None
        self.url_map.connect(name, rule, **kwargs)

    def expose(self, rule, name=None, **kwargs):
        def decorator(func):
            kwargs['_endpoint'] = func
            kwargs['_module'] = None
            self.url_map.connect(name or func.__name__, rule, **kwargs)
            return func

        return decorator

    def __call__(self, environ, start_response):
        request = self.Request(self, environ)
        try:
            result = self.url_map.match(None, environ)
            if not result:
                raise HTTPNotFound()

            try:
                endpoint = result.pop('_endpoint')
            except KeyError:
                return result.pop('_wsgi')(environ, start_response)

            request.module = result.pop('_module', None)
            response = endpoint(request, **result)
            if isinstance(response, basestring):
                response = self.Response(response)
        except HTTPException, e:
            response = e

        if request.session is not None:
            request.session.save()

        return response(environ, start_response)

    def run(self, host='localhost', port=8000):
        httpd = make_server(host, port, self)
        httpd.serve_forever()

    def set_renderer(self, renderer):
        self._renderer = renderer

    def render(self, request, name, result):
        result.setdefault('url_for', request.url_for)
        result.setdefault('request', request)
        result.setdefault('get_flashed_messages', request.get_flashed_messages)

        response = self._renderer(self.Response, name, result)

        for k, v in result.iteritems():
            if k.startswith('http_'):
                setattr(response, k[5:], v)

        return response

    def renderer(self, name, **kwargs):
        def inner(func):
            @wraps(func)
            def inner2(request, *iargs, **ikwargs):
                result = func(request, *iargs, **ikwargs)
                if isinstance(result, Response):
                    return result
                args = kwargs.copy()
                args.update(result)
                return self.render(request, name, args)

            return inner2

        return inner

    def add_module(self, module):
        if isinstance(module, str):
            module = get_from_module(module, 2)

        module.attach(self)


class Module(object):
    def __init__(self, name, prefix=None):
        self.name = name
        self.rules = []
        self.renderers = []
        self.prefix = prefix

    def expose(self, rule, name=None, **kwargs):
        def decorator(func):
            if rule[0] != '/':
                rrule = self.prefix + rule
            else:
                rrule = rule

            kwargs['_endpoint'] = func
            kwargs['_module'] = self.name
            self.rules.append((get_full_name(self.name, name or func.__name__), rrule, kwargs))
            return func

        return decorator

    def renderer(self, name, **kwargs):
        def inner(func):
            @wraps(func)
            def inner2(request, *iargs, **ikwargs):
                result = func(request, *iargs, **ikwargs)
                if isinstance(result, Response):
                    return result
                args = kwargs.copy()
                args.update(result)
                return self.app.render(request, name, args)

            return inner2

        return inner

    def attach(self, app):
        self.app = app

        for rname, rule, kwargs in self.rules:
            app.url_map.connect(rname, rule, **kwargs)
