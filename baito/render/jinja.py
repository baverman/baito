from jinja2 import Environment, PackageLoader, StrictUndefined

class Renderer(object):
    def __init__(self, package, folder='templates'):
        self.env = Environment(
            loader=PackageLoader(package, 'templates'),
            undefined = StrictUndefined,
            extensions = ['jinja2.ext.with_']
        )

    def __call__(self, Response, name, result):
        template = self.env.get_template(name)
        return Response(template.render(result))

