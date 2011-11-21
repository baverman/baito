import sys

def get_from_module(name, call_level=1):
    globs = sys._getframe(call_level).f_globals
    module, _, func_name = name.rpartition('.')
    module_name = module.lstrip('.')
    level = len(module) - len(module_name)

    module = __import__(module_name, globals=globs, level=level)
    if not level:
        module = sys.modules[module_name]

    try:
        return getattr(module, func_name)
    except AttributeError:
        raise AttributeError("module '%s' has no attribute '%s'" % (module.__name__, func_name))

