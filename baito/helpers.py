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
    form = cls(request.form, *args, **kwargs)
    if request.method == 'POST' and form.validate():
        return True, form
    else:
        return False, form

wtforms.Form.get_simple_fields = get_simple_fields
wtforms.Form.get_submit_fields = get_submit_fields
wtforms.Form.get_hidden_fields = get_hidden_fields
wtforms.Form.fill = classmethod(fill_form)
