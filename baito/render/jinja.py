from jinja2 import Environment, PackageLoader
from webob import Response

class Renderer(object):
    def __init__(self, package, folder='templates'):
        self.env = Environment(loader=PackageLoader(package, 'templates'))

    def __call__(self, name, value, *args, **kwargs):
        template = self.env.get_template(name)
        return Response(template.render(value))

