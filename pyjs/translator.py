import ast
import os
import sys

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

class Visitor(ast.NodeVisitor):

    def __init__(self, py_module, modules, name=None, output=sys.stdout):
        self._name = name or py_module.__name__
        self._o = py_module
        self._modules = modules
        self._out = output

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
        if node.args or node.kwargs or node.starargs:
            raise NotImplementedError
        self.visit(node.func)
        self._s('()')

    def visit_Expr(self, node):
        # this just adds semicolons to the end of any expression
        self.visit(node.value)
        self._l(';')

    def visit_FunctionDef(self, node):
        fqn = self._o.__name__ + '.' + node.name;
        self._w(fqn + ' = function (')
        self.visit(node.args)
        self._l(') {')
        for n in node.body:
            self.visit(n)
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
        #import pdb;pdb.set_trace()
        for t in node.targets:
            self.visit(t)
        self._s('=')
        self.visit(node.value)
        self._l(';')
        #return self.generic_visit(node)

    def visit_Name(self, node):
        self._s(self._o.__name__ + '.' + node.id)
        return self.generic_visit(node)

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



