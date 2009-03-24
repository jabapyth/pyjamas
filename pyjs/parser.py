from ast import *
import util
import sys, os

class PathAnalyzer(NodeVisitor):

    def __init__(self, name, leafs_only=False):
        self.path = ''
        self.name = name
        self.path2node = {}
        self.node2path = {}
        self.leafs_only = leafs_only

    def visit_Module(self, node):
        self.path += self.name
        self.path2node[self.path] = node
        self.node2path[node] = self.path
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        old_path = self.path
        self.path += '.' + node.name
        if self.leafs_only:
            parent = self.path2node.get(old_path)
            if parent:
                del self.path2node[old_path]
                del self.node2path[parent]
        self.path2node[self.path] = node
        self.node2path[node] = self.path
        self.generic_visit(node)
        self.path = old_path

    visit_ClassDef = visit_FunctionDef

    def visit(self, node):
        super(PathAnalyzer, self).visit(node)

class DepAnalyzer(NodeVisitor):

    def __init__(self, base_deps=['pyjslib']):
        self.dependencies = {}
        self.order = []
        for mod in base_deps:
            self._add_dep(mod)

    def _add_dep(self, module):
        if module in self.order:
            return
        da = DepAnalyzer(base_deps=[])
        changed, tree = get_tree(module)
        da.visit(tree)
        for name, path in da.getDeps():
            if name not in self.order:
                self.order.append(name)
                self.dependencies[name] = path
        p = util.module_path(module)
        if not p:
            raise Exception, 'No module found for alias %s' % dump(node)
        self.dependencies[module] = p
        if not module in self.order:
            self.order.append(module)

    def visit_Import(self, node):
        for alias in node.names:
            self._add_dep(alias.name)

    def visit_ImportFrom(self, node):
        self._add_dep(node.module)
        for alias in node.names:
            # look if we have a  module
            candidate = node.module + '.' + alias.name
            p = util.module_path(candidate)
            # look if the name is a module
            if p:
                tail = os.path.sep.join(candidate.split('.'))
                if p.endswith(tail + '.py'):
                    self._add_dep(candidate)

    def getDeps(self):
        res = []
        for name in self.order:
            res.append((name, self.dependencies[name]))
        return res

class Merger(NodeTransformer):

    def __init__(self, overrides):
        self.overrides = overrides

    def visit_FunctionDef(self, node):
        o = self.overrides.get(node)
        if o:
            return o
        return node

    visit_ClassDef = visit_FunctionDef

def get_deps(base_module, platform=None):
    path = util.module_path(base_module)
    changed, tree = get_tree(mod, platform)
    da = DepAnalyzer()
    da.visit(tree)
    from pprint import pprint
    res = []
    exists = False
    for name, p in da.getDeps():
        if name == base_module:
            exists = True
        res.append((name, p))
    if not exists:
        res.append((base_module, path))
    return res

_tree_cache = {}
def get_tree(base_module, platform=None):
    """returns a tuple (changed, tree) where tree is the merged tree
    from platform overrides of module_name. changed is True if
    overrides where applied"""
    k = (base_module, platform)
    global _tree_cache
    if k in _tree_cache:
        return _tree_cache[k]
    base_p = util.module_path(base_module)
    if not base_p:
        raise Exception, "Module not found %r" % base_module
    plat_p = None
    if platform:
        plat_module = '__plat_%s__.%s' % (platform, base_module)
        plat_p = util.module_path(plat_module)
    base_f = open(base_p)
    base_tree = parse(base_f.read(), base_p)
    base_f.close()
    if not plat_p:
        _tree_cache[k] = (False, base_tree)
        return _tree_cache[k]
    plat_f = open(plat_p)
    plat_tree = parse(plat_f.read(), plat_p)

    base_a = PathAnalyzer(base_module)
    plat_a = PathAnalyzer(plat_module, leafs_only=True)

    base_a.visit(base_tree)
    plat_a.visit(plat_tree)
    overrides = {}
    for p, node in base_a.path2node.items():
        op = '__plat_%s__.%s' % (platform, p)
        if op in plat_a.path2node:
            overrides[node] = plat_a.path2node[op]
    m = Merger(overrides)
    tree = m.visit(base_tree)
    _tree_cache[k] = (True, tree)
    return _tree_cache[k]

if __name__ == '__main__':
    mod = sys.argv[1]
    from pprint import pprint
    pprint(get_deps(mod))

