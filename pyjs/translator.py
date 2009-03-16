import ast
import os
import sys

def translate(py_module, modules, out_file, tree=None):
    path = os.path.abspath(py_module.__file__)
    if path.endswith('.pyc'):
        path = path[:-1]
    if not tree:
        f = open(path)
        src = f.read()
        f.close()
        tree = ast.parse(src, path)
    v = Visitor(py_module, modules)
    v.visit(tree)
    from pprint import pprint
    pprint(ast.dump(tree))

class Visitor(ast.NodeVisitor):

    def __init__(self, py_module, modules, output=sys.stdout):
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
        self._s(self._o.__name__)
        self._l('= function() {')
        self._l(self._o.__name__ + '.__name__ = ' + self._o.__name__ + ';')
        self.generic_visit(node)
        self._l('}')

    def visit_FunctionDef(self, node):
        #import pdb;pdb.set_trace()
        #self._p(node.name)
        return self.generic_visit(node)

    def visit_Name(self, node):
        return self.generic_visit(node)

    def visit_Const(self, node):
        print node

    def visit_Num(self, node):
        self._s(node.n)
