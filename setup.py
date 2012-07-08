from setuptools import setup, find_packages

setup(
    name     = 'baito',
    version  = '0.3dev',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Lightweight WSGI framework. Explicit thin wrapper around WebOb, Beaker and Routes',
    zip_safe   = False,
    packages = find_packages(exclude=['tests']),
    url = 'http://github.com/baverman/baito',
)