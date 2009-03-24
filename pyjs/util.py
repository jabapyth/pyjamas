from ast import *
import os
import sys

_path_cache= {}
def module_path(name, path=None):
    path = path or sys.path
    global _path_cache
    k = (name, tuple(sorted(path)))
    if k in _path_cache:
        return _path_cache[k]
    parts = name.split('.')
    candidates = []
    tail = []
    packages = {}
    modules = {}
    for pn in parts:
        tail.append(pn)
        for p in path:
            cp = os.path.join(*([p] + tail))
            if os.path.isdir(cp) and os.path.exists(
                os.path.join(cp, '__init__.py')):
                packages['.'.join(tail)] = os.path.join(cp, '__init__.py')
            elif os.path.exists(cp + '.py'):
                modules['.'.join(tail)] = cp + '.py'
    res = None
    if modules:
        assert len(modules)==1
        res = modules.values()[0]
    elif packages:
        res = packages[sorted(packages)[-1]]
    _path_cache[k] = res
    return res

if __name__ == '__main__':
    mod = sys.argv[1]
    path = module_path(mod)
    if not path:
        raise Exception, "Module not found %s" % mod
    print path

