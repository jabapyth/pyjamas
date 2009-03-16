import types

def getWrapper(o):
    for w in (Module, Function, Klass):
        if type(o) in w.types:
            return w(o)
    print "not a wrappable object", o
    return o


class PyObj:

    types = ()

    def get(self, name):
        """returns the object with given name"""
        o = self.o.__dict__.get(name)
        if o:
            return getWrapper(o)

class Callable(PyObj):
    pass

class Module(PyObj):
    """represents a module"""

    types = (types.ModuleType,)

    def __init__(self, o, tree=None):
        assert type(o) is types.ModuleType
        self.o = o
        self.name = self.o.__name__
        self.prefix = self.name + '.'
        self.tree = tree

class Function(Callable):

    """a python funciton wrapper"""

    types = (types.FunctionType,
             types.BuiltinMethodType,
             types.BuiltinFunctionType)

    def __init__(self, o):
        assert type(o) in self.types, str(o)
        self.o = o
        if self.o.__module__ == '__builtin__':
            m = 'pyjslib'
        else:
            m = self.o.__module__
        self.name = m + '.' + self.o.__name__
        self.js_call_name = self.name
        self.js_o_name = self.name


class Klass(Callable):
    """represents a class object"""

    types = (types.ClassType, types.TypeType)

    def __init__(self, o):
        assert type(o) in self.types, str(o)
        self.o = o
        self._init()

    def _init(self):

        if self.o.__module__ in ('__builtin__', 'exceptions'):
            self.mod_name = 'pyjslib'
        else:
            self.mod_name = self.o.__module__
        self.js_c_name = self.mod_name + '.' +self.o.__name__
        self.js_name = self.mod_name + '.__' +self.o.__name__
        if self.o.__bases__:
            if len(self.o.__bases__)>1:
                raise TranslationError('Only one base allowed %s' % self.o)
            self.base = getWrapper(self.o.__bases__[0])
        else:
            self.base = None
        # the prototype class
        self.js_o_name = self.js_name + '.prototype.__class__'
        self.js_call_name = self.js_c_name

    def __repr__(self):
        return '<Klass for %r> ' % self.o

