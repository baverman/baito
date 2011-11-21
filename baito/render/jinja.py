from jinja2 import Environment, PackageLoader

class Renderer(object):
    def __init__(self, package, folder='templates'):
        self.env = Environment(loader=PackageLoader(package, 'templates'))

    def __call__(self, Response, name, result):
        template = self.env.get_template(name)
        return Response(template.render(result))

