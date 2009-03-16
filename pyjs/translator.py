import ast
import os
import sys
import wrappers

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
    from pprint import pprint
    pprint(ast.dump(tree))

undefined = object()

class Visitor(ast.NodeVisitor):

    def __init__(self, py_module, modules, name=None, output=sys.stdout):
        self._name = name or py_module.__name__
        self._o = py_module
        self._modules = modules
        self._out = output
        self._locals = set()

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
        self._l('//---- start module ' + self._o.__name__ + ' ----//')
        self._s(self._o.__name__)
        self._l('= function() {')
        self._l(self._o.__name__ + '.__name__ = "' + self._name + '";')
        self.generic_visit(node)
        self._l('};')
        self._l('//---- end module ' + self._o.__name__ + ' -----//')

    def visit_Call(self, node):
        if node.kwargs or node.starargs:
            raise NotImplementedError
        if not isinstance(node.func, ast.Name):
            raise NotImplementedError, node.func
        #name = self._fq_name(node.func)
        #import pdb;pdb.set_trace()
        fo = wrappers.getWrapper(self._o.__dict__[node.func.id])
        if not isinstance(fo, wrappers.Function):
            raise NotImplementedError, node
        var_names = fo.o.func_code.co_varnames
        # gather keyword args
        keywords = {}
        for n in node.keywords:
            keywords[n.arg] = n.value
        js_args = []
        for pos, var_name in enumerate(var_names):
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

    def visit_ClassDef(self, node):
        if len(node.bases)>1:
            raise NotImplementedError, node

        # get the python object wrapper
        klass = wrappers.getWrapper(self._o.__dict__[node.name])

        # the class object
        self._l(klass.js_name + ' = function () {};')

        # the constructor
        self._l(klass.js_c_name + ' = function () {')
        self._l("var instance = new " + klass.js_name + "();")
        self._l("if (instance.__init__) "
                "{instance.__init__.apply(instance, arguments)};")
        self._l("return instance;")
        self._l("};")

        # set the name
        self._l(klass.js_c_name + '.__name__ = "' + node.name + '";')

        # initializer
        init_name = klass.js_name + '_initialize'
        self._l(init_name + ' = function() {')
        self._l('if(%s.__was_initialized__) {return;};' % klass.js_name)
        self._l('%s.__was_initialized__ = true;' % klass.js_name)
        # TODO: bases
        #self._l('if(%s.__was_initialized__) {return;};' % klass.js_name)

        if klass.base:
            assert node.bases
            self._s("if(!"+klass.base.js_name+".__was_initialized__) {")
            self._l(klass.base.js_name+"_initialize();};")
            self._l("pyjs_extend(" + klass.js_name + ", "+ klass.base.js_name + ");")
        self._l('%s.__new__ =  %s;' % (klass.js_o_name,klass.js_c_name))
        self._l('%s.__name__ =  "%s";' % (klass.js_o_name,node.name))
        self._l('};')
        self._l(klass.js_name+"_initialize();")

    def visit_FunctionDef(self, node):
        fqn = self._o.__name__ + '.' + node.name;
        self._l(fqn + ' = function () {')
        # get the params
        fo = wrappers.getWrapper(self._o.__dict__[node.name])
        if not isinstance(fo, wrappers.Function):
            raise NotImplementedError, node
        #self.visit(node.args)
        #self._l(') {')
        old_locals = self._locals
        self._locals = set()
        offset = len(node.args.defaults)-len(node.args.args)*2+1
        for pos, arg in enumerate(node.args.args):
            if not isinstance(arg, ast.Name):
                raise NotImplementedError, arg
            try:
                default = node.args.defaults[offset+pos]
            except IndexError:
                default = undefined
            self._s('var')
            self._s(arg.id)
            self._locals.add(arg.id)
            self._s('= arguments[%s]' % pos)
            if default is not undefined:
                self._s('||'), self.visit(default)
            self._l(';')

        for n in node.body:
            self.visit(n)
        self._locals = old_locals
        #self.generic_visit(node)
        self._l('};')
        # assign __name__ field
        self._l(fqn + ".__name__ = '" + node.name + "';")


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
        #return self.generic_visit(node)


    def _fq_name(self, node):
        # XXX not ready
        return self._o.__name__ + '.' + node.id

    def visit_Name(self, node, pyo=None):
        if node.id in self._locals:
            name = node.id
        else:
            name = self._fq_name(node)
        self._s(name)

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
        #import pdb;pdb.set_trace()

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



