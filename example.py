#!/usr/bin/env python
from baito import App
app = App()

@app.expose('/')
def hello(request):
    return 'Hello World'

app.run()