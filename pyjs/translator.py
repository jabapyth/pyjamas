import ast
import os
import sys
import wrappers

LITERALS = {
    'True': 'true',
    'False': 'false',
    'None': 'null'
    }


def translate(py_module, modules, out_file, tree=None, name=None):
    path = os.path.abspath(py_module.__file__)
    if path.endswith('.pyc'):
        path = path[:-1]
    if not tree:
        f = open(path)
        src = f.read()
        f.close()
        tree = ast.parse(src, path)
    v = Visitor(py_module, modules, name=name, output=out_file)
    v.visit(tree)
    #from pprint import pprint
    #pprint(ast.dump(tree))

undefined = object()

class Visitor(ast.NodeVisitor):

    def __init__(self, py_module, modules, name=None,
                 output=sys.stdout):
        self.globals = py_module.__dict__.copy()
        self.name = self.globals['__name__'] = name or py_module.__name__
        self.locals = {}
        #self.name = py_module.__name__
        self.module = py_module
        self.modules = modules
        self._out = output
        self.ctx = None
        self.self_name = None
        self.defined_globals = set()

    def _l(self, s):
        """print to out with newline"""
        print >>self._out, s

    def _s(self, s):
        """print to out with space"""
        print >>self._out, s,

    def _w(self, s):
        """write to out without any whitespace"""
        self._out.write(s)

    # visitors
    def visit_Module(self, node):
        self.ctx = node
        name = self.globals['__name__']
        self._l('//---- start module %s ----//' % name)
        self._s(self.globals['__name__'])
        self._l('= function() {')
        self._l(name+ '.__name__ = "%s";' % name)
        self.generic_visit(node)
        self._l('};')
        self._l('//---- end module %s -----//' % name)
        self.ctx = None

    def visit_List(self, node):
        self._s('new pyjslib.List([')
        for pos, n in enumerate(node.elts):
            self.visit(n)
            if pos+1<len(node.elts):
                self._s(',')
        self._w('])')

    def visit_Dict(self, node):
        self._s('new pyjslib.Dict([')
        for pos, k in enumerate(node.keys):
            v = node.values[pos]
            self._w('[')
            self.visit(k)
            self._s(',')
            self.visit(v)
            self._w(']')
            if pos+1<len(node.keys):
                self._s(',')
        self._w('])')

    def _visit_list(self, iterable, seperator=','):
        if not iterable:
            return
        first = True
        for v in iterable:
            if not first:
                self._s(seperator)
            first = False
            self.visit(v)

    def visit_Discard(self, node):
        raise NotImplementedError

    def visit_Call(self, node):
#         if node.starargs:
#             raise NotImplementedError
        # look if we have the native js func
        if isinstance(node.func, ast.Name):
            name = self._get_name(node.func)
            if name == '__pyjamas__.JS':
                self._l(node.args[0].s)
                return
        self.visit(node.func)
        self._w('(')
        self._visit_list(node.args)
        self._s(')')

        return
        self._js_array(node.args)
        self._s(',')
        self._js_array(node.keywords)
        self._s(',')
        if node.starargs:
            self.visit(node.starargs)
        else:
            self._w('undefined')
        self._s(',')
        if node.kwargs:
            self.visit(node.kwargs)
        else:
            self._w('undefined')
        self._l(');')
        return
        import pdb;pdb.set_trace()
        if isinstance(node.func, ast.Name):
            o = self.ctx.get(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            o = self.ctx.get(node.func.value.id)
            #raise NotImplementedError, node.func
        #name = self._fq_name(node.func)
        #import pdb;pdb.set_trace()

        if isinstance(o, wrappers.Function):
            fo = o
        elif isinstance(o, wrappers.Klass):
            fo = o.get('__init__')
            if not fo:
                # no init method so just the constructor
                self._s(o.js_name + '()')
                return
            elif isinstance(fo, wrappers.Method):
                #import pdb;pdb.set_trace()
                #raise NotImplementedError
                pass
            else:
                raise NotImplementedError, fo
        else:
            raise NotImplementedError, (o, node)

        # check if the args match
        if len(node.args)<fo.required:
            raise TypeError(
                '%s requires at least %s non-keyword args %s' % (
                    node.func.id, fo.required, fo.o.func_code))
        # gather keyword args
        keywords = {}
        for n in node.keywords:
            keywords[n.arg] = n.value
        js_args = []
        for pos, var_name in enumerate(fo.var_names):
            try:
                vn = node.args[pos]
            except IndexError:
                if var_name in keywords:
                    vn = keywords[var_name]
                else:
                    vn = undefined
            js_args.append(vn)
        self._s(fo.js_call_name + '(')
        for i, a in enumerate(js_args):
            if a is undefined:
                self._s('undefined')
            else:
                self.visit(a)
            if i+1<len(js_args):
                self._s(',')
        self._s(')')

    def visit_Expr(self, node):
        # this just adds semicolons to the end of any expression
        self.visit(node.value)
        self._l(';')

    def visit_Return(self, node):
        self._s('return')
        self.visit(node.value)
        self._l(';')

    def visit_Attribute(self, node):
        self.visit(node.value)
        self._w('.' + node.attr)

    def visit_ClassDef(self, node):
        if len(node.bases)>1:
            raise NotImplementedError, node

        # get the python object wrapper
        klass = wrappers.getWrapper(self.globals[node.name])
        # the class object
        js_name = self.name + '.__' + node.name
        c_name = self.name + '.' + node.name
        self._l(js_name + ' = function () {};')

        # the constructor
        self._l(c_name + ' = function () {')
        self._l("var instance = new " + js_name + "();")
        self._l("if (instance.__init__) "
                "{instance.__init__.apply(instance, arguments)};")
        self._l("return instance;")
        self._l("};")

        # set the name
        self._l(c_name + '.__name__ = "' + node.name + '";')

        # initializer
        init_name = js_name + '_initialize'
        self._l(init_name + ' = function() {')
        self._l('if(%s.__was_initialized__) {return;};' % js_name)
        self._l('%s.__was_initialized__ = true;' % js_name)
        # TODO: bases
        #self._l('if(%s.__was_initialized__) {return;};' % js_name)

        # derive from self if no base
        if klass.base:
            self._s("if(!"+klass.base.js_name+".__was_initialized__) {")
            self._l(klass.base.js_name+"_initialize();};")
            self._l("pyjs_extend(" + js_name + ", "+ klass.base.js_name + ");")
        else: # XXX hack alarm we need a superclass
            self._s("if(!"+js_name+".__was_initialized__) {")
            self._l(js_name+"_initialize();};")
            self._l("pyjs_extend(" + js_name + ", "+ js_name + ");")

        ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self.ctx = ctx
        proto_name = '%s.__%s.prototype.__class__' % (self.name, node.name)
        self._l('%s.__new__ =  %s;' % (proto_name, c_name))
        self._l('%s.__name__ =  "%s";' % (proto_name, node.name))
        self._l('};')
        self._l(js_name+"_initialize();")

    def visit_MethodDef(self, node):
        old_self = self.self_name
        old_locals = self.locals
        args = node.args.args[1:]
        defaults = node.args.defaults
        if len(defaults)>len(args):
            raise Exception('cannot use self with defaults %s', node.lineno)
        if not isinstance(node.args.args[0], ast.Name):
            raise NotImplementedError, "self attr is no name"
        self.self_name = node.args.args[0].id
        fqn = '%s.__%s.prototype.__class__.%s' % (self.name, self.ctx.name,
                                                  node.name)
        self._s(fqn + ' = function (')
        self._visit_list(args)
        self._l('){')
        self._func_defaults(args, defaults)
        old_ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self._l('};')
        self.ctx = old_ctx

        js_i_name =  '%s.__%s.prototype.%s' % (self.name, self.ctx.name,
                                               node.name)
        self._l(fqn + '.unbound_method = true;')

        self._l(fqn + ".__name__ = '%s';" % node.name)
        self._l(js_i_name + ".__name__ = '%s';" % node.name)
        self._l(js_i_name + '.instance_method = true;')

        self.self_name = old_self
        self.locals = old_locals

    def _func_defaults(self, args, defaults):
        # prints out default defs like
        # if (typeof c == 'undefined') c=1;
        for arg, default in zip(reversed(args),
                                reversed(defaults)):
            self._s("if (typeof")
            self.visit(arg)
            self._s(" === 'undefined')")
            self.visit(arg)
            self._s("=")
            self.visit(default)
            self._l(';')

    def visit_FunctionDef(self, node):

        """
        ('name', 'args', 'body', 'decorator_list')
        """

        if isinstance(self.ctx, ast.ClassDef):
            return self.visit_MethodDef(node)
        if not isinstance(self.ctx, ast.Module):
            raise NotImplementedError, self.ctx
        old_locals = self.locals
        old_self = self.self_name
        self.self_name = None

        args = node.args.args
        defaults = node.args.defaults

        fqn = self.name + '.' + node.name
        self._s(fqn + ' = function (')
        self._visit_list(args)
        self._l('){')

        self._func_defaults(node.args.args, node.args.defaults)

        old_ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self._l('};')
        self.ctx = old_ctx

        self.defined_globals.clear()
        self.self_name = old_self
        self.locals = old_locals

    def visit_Print(self, node):
        # XXX this is ms specific
        self._s('print(')
        for n in node.values:
            self.visit(n)
        self._l(');')

    def visit_Assign(self, node):
        for t in node.targets:
            self.visit(t)
            self._s('=')
            self.visit(node.value)
            self._l(';')

    def visit_Global(self, node):
        self.defined_globals.update(node.names)

    def _get_name(self, node):
        # look in class, this stays the same
        print "_get_name", node.id, self.ctx, node.ctx, node.lineno
        res = None
        if node.id in LITERALS:
            if isinstance(node.ctx, ast.Store):
                raise Excpetion('Cannot assign to reserved name')
            return LITERALS[node.id]
        elif isinstance(node.ctx, ast.Param):
            self.locals[node.id] = node
            return node.id
        elif isinstance(self.ctx, ast.Module):
            if isinstance(node.ctx, ast.Store):
                self.globals[node.id] = node
            return self.name + '.' +  node.id
        elif isinstance(self.ctx, ast.FunctionDef):
            if node.id == self.self_name:
                return 'this'
            if isinstance(node.ctx, ast.Store):
                if node.id in self.defined_globals:
                    return self.name + '.' + node.id
                self.locals[node.id] = node
                return 'var ' + node.id
            elif isinstance(node.ctx, ast.Load):
                if node.id in self.locals:
                    return node.id
                elif node.id in self.globals:
                    return self.name + '.' +  node.id
                else:
                    raise LookupError, "Name not found", node.lineno
            else:
                raise NotImplementedError, node
        elif isinstance(self.ctx, ast.ClassDef):
            return '.'.join((self.name,
                             '__' +  self.ctx.name,
                             'prototype',
                             '__class__',
                             node.id))
        raise NotImplementedError, (node.id, self.ctx, node.ctx)

    def visit_Name(self, node):
        self._s(self._get_name(node))

    def visit_Const(self, node):
        print node

    def visit_Num(self, node):
        self._s(node.n)

    def visit_Pass(self, node):
        pass

    def visit_Compare(self, node):
        if len(node.comparators)>1:
            raise NotImplementedError
        self.visit(node.left)
        self.visit(node.ops[0])
        self.visit(node.comparators[0])

    def visit_Str(self, node):
        self._s("'" + node.s + "'")

    def visit_If(self, node):
        self._s('if (')
        self.visit(node.test)
        self._l(') {')
        for n in node.body:
            self.visit(n)
        self._l('};')
        if node.orelse:
            raise NotImplementedError

    # comparison operators
    # cmpop = Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn
    def visit_Eq(self, node):
        self._s('===')

    def visit_NotEq(self, node):
        self._s('!==')



