from webob.exc import HTTPRedirection
from functools import wraps
import wtforms

def get_simple_fields(self):
    for f in self:
        if not getattr(f, 'norender', False) and f.widget.__class__.__name__ != 'SubmitInput' and f.__class__.__name__ != 'HiddenField':
            yield f

def get_submit_fields(self):
    for f in self:
        if f.widget.__class__.__name__ == 'SubmitInput':
            yield f

def get_hidden_fields(self):
    for f in self:
        if f.__class__.__name__ == 'HiddenField':
            yield f

def fill_form(cls, request, *args, **kwargs):
    form = cls(request.POST, *args, **kwargs)
    if request.method == 'POST' and form.validate():
        return True, form
    else:
        return False, form

wtforms.Form.get_simple_fields = get_simple_fields
wtforms.Form.get_submit_fields = get_submit_fields
wtforms.Form.get_hidden_fields = get_hidden_fields
wtforms.Form.fill = classmethod(fill_form)

def back_url(func_or_default_name, value=None, **kwargs):
    def inner(func):
        @wraps(func)
        def decorator(request, *args, **kwargs):
            result = func(request, *args, **kwargs)
            if result:
                return result

            url = request.GET.get('back', None)
            if not url and func_or_default_name:
                url = request.url_for(func_or_default_name, value, **kwargs)

            if not url:
                raise Exception('There is no any back url. Provide default one')

            return request.redirect(url)

        return decorator

    if callable(func_or_default_name):
        func = func_or_default_name
        func_or_default_name = None
        return inner(func)
    else:
        return inner