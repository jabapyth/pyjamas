def repr(o):
    f = getattr(o, '__repr__', None)
    if not f:
        f = getattr(o, 'toString', None)
    if callable(f):
        return f()
    return o

def printFunc(objs):
    JS("""
        var s = "";
        for(var i=0; i < objs.length; i++) {
            if(s != "") s += " ";
                s += pyjslib.repr(objs[i]);
        }

        print(s);
    """)

def import_module(self, parent_name, module_name):
    pass

