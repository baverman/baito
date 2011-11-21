from jinja2 import Environment, PackageLoader, StrictUndefined

class Renderer(object):
    def __init__(self, package, folder='templates', **kwargs):
        kwargs.update({
            'undefined': StrictUndefined,
            'extensions': ['jinja2.ext.with_'],
            'line_statement_prefix': '#',
            'line_comment_prefix': '##',
        })

        self.env = Environment(
            loader=PackageLoader(package, 'templates'),
            **kwargs
        )

    def __call__(self, Response, name, result):
        template = self.env.get_template(name)
        return Response(template.render(result))

