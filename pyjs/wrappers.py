import types

def getWrapper(o):
    for w in (Module, Function, Klass, Method):
        if type(o) in w.types:
            return w(o)
    raise NotImplementedError, (o, type(o))

class PyObj:

    types = ()

    def __init__(self, o):
        import pdb;pdb.set_trace()
        self.o = o

    def get(self, name):
        """returns the object with given name"""
        o = None
        if name in self.o.__dict__:
            o = getattr(self.o, name)
        #o = self.o.__dict__.get(name)
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
        self.var_names = self.o.func_code.co_varnames
        # number or required non-keyword args
        self.required = len(self.var_names)-len(self.o.func_defaults or [])

    def __repr__(self):
        return "<wrappers.Function %s>" % self.o.func_code

class Method(Callable):
    """a python method wrapper"""
    types = (types.MethodType,)
    def __init__(self, o):
        assert type(o) in self.types, str(o)
        self.o = o
        self.klass = getWrapper(self.o.im_class)
        self.function = getWrapper(self.o.im_func)
        self.required = self.function.required-1
        self.var_names = self.function.var_names[1:]
        if self.o.__name__ == '__init__':
            self.js_call_name = self.klass.js_call_name
        else:
            ## XXX test this
            self.js_call_name = self.klass.js_call_name + '.' +self.o.__name__
        self.js_o_name = self.js_call_name
        

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
        # name of the instance object
        self.js_i_name = self.js_name + '.prototype'
        self.js_call_name = self.js_c_name

    def __repr__(self):
        return '<Klass for %r> ' % self.o

