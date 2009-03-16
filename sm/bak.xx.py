import imputil
import pyjs
import os
import sys
import cStringIO
import compiler
import types
import shutil
import re
from compiler import ast

PAT_PLAT_MODULE = re.compile(r'^__plat_(\w+)__\.(.+)$')

def importModule(fqname):
    """returns a list of modules and packages needed to import fqname"""
    parts = fqname.split('.')
    if len(parts)==1:
        # normal toplevel import
        return [__import__(parts[0])]
    # import all packages and the module
    mods = []
    # first import the toplevel package
    mods.append(__import__(parts[0]))
    # not the deeper modules
    for pos in range(len(parts)-1):
        parents = parts[:pos+1]
        leafs = parts[pos+1:pos+2]
        parent = '.'.join(parents)
        p = __import__(parent, {}, {}, leafs)
        if leafs:
            m = getattr(p, leafs[0])
        else:
            m = p
        mods.append(m)
    return mods


class ImportManager(imputil.ImportManager):

    """this importer is needed to get the order of modules"""
    _order = []
    _modules = {}

    def __init__(self, platforms=[]):
        self._platforms = platforms
        imputil.ImportManager.__init__(self)

    def _import_hook(self, fqname, globals=None, locals=None, fromlist=None):
        if fqname in self._order:
            return
        res =  imputil.ImportManager._import_hook(self, fqname, globals,
                                                  locals, fromlist)
        self._addModule(fqname, res, globals, locals)
        for m in sys.modules:
            # check if we have missed an imported module or a package
            if not PAT_PLAT_MODULE.match(m) and m not in self._order:
                self._addModule(m, sys.modules[m], {}, {})
        return res

    def _addModule(self, fqname, m, g, l):
        # __pyjamas__ is the python fixture for the js modules
        if fqname!='__pyjamas__' and fqname not in self._modules:
#            f = getattr(m,'__file__', '')
#            #print "_addModule", fqname, f, m
#             if f and f.endswith('.pyc'):
#                 f = f[:-1]
#                 f = os.path.abspath(f)
            self._moduls[fqname] = m
            self._order.append(fqname)

    def getModules(self):
        return self._order, self._paths
        res =[]
        for m in self._order:
            res.append((m, self._paths[m]))
        return res

class TreeCompiler(object):

    def __init__(self, top_module, output='output',
                 debug=False, js_libs=[], platforms=[]):
        self.js_path = os.path.abspath(output)
        self.top_module = top_module
        self.debug = debug
        self.js_modules = {}
        self.js_libs = map(os.path.abspath, js_libs)
        self.platforms = platforms
        self.plat_modules = {}

    @staticmethod
    def _import(module_name, mgr=None, froms=[]):
        l = {}
        g = {}
        old_path = sys.path[:]
        sys.path = pyjs.path[:]
        if mgr:
            mgr.install()
        try:
            m = __import__(module_name, g, l, froms)
            return m, g, l
        finally:
            if mgr:
                mgr.uninstall()
            sys.path = old_path

    def gatherModules(self):
        # all standard modules
        mgr = ImportManager(self.platforms)
        sys.modules = {}
        self._import(self.top_module, mgr)
        self.module_order, self.modules = mgr.getModules()

        # import the platform modules
        for plat in self.platforms:
            self.plat_modules[plat] = {}
            for mod in self.module_order:
                pmod = '__plat_%s__.%s' % (plat, mod)
                print pmod
                ms = []
                old_path = sys.path[:]
                sys.path = pyjs.path[:]
                try:
                    ms = importModule(pmod)
                except (ImportError, AttributeError), e:
                    if pmod in str(e):
                        continue
                finally:
                    sys.path = old_path
                self.plat_modules[plat][mod] = ms[-1:]
        print self.plat_modules

    def build(self):
        if not os.path.isdir(self.js_path):
            os.mkdir(self.js_path)
        self.module_order = []
        self.modules = {}
        self._copyJS()
        self.gatherModules()
        self.translateAll()

    def _copyJS(self):
        for src in self.js_libs:
            dst = os.path.join(self.js_path, os.path.basename(src))
            shutil.copyfile(src, dst)


    def link(self, platform=None):
        entry_file = self.js_modules[self.top_module]
        f = open(entry_file, 'a')
        print >>f, "//---- initialization --- //"
        for jsf in self.js_libs:
            print >>f, "load('%s');" % jsf
        done = set()
        for mod in self.module_order:
            plat_mod = self.plat_mods[platform].get(mod)
            if mod in done:
                continue
            done.add(mod)
            plat_mod = '__plat_%s__.%s' % (platform, mod)
            if plat_mod in self.module_order:
                mod_name = mod
                mod = plat_mod
                done.add(plat_mod)
            else:
                mod_name = mod
            pm = PAT_PLAT_MODULE.match(mod)
            if pm:
                if pm.group(1) != platform:
                    continue
            p = self.js_modules[mod]

            if entry_file == p:
                continue
            print >>f, "load('%s');" % p
            print >>f, '%s();' % mod_name
        print >>f, "//---- included js_libs --- //"
        # main
        print >>f, '%s();' % self.top_module
        f.close()

    def merge_ast(self, tree1, tree2):
        for child in tree2.node:
            if isinstance(child, ast.Function):
                self.replaceFunction(tree1, child.name, child)
            elif isinstance(child, ast.Class):
                self.replaceClassMethods(tree1, child.name, child)

        return tree1

    def replaceFunction(self, tree, function_name, function_node):
        # find function to replace
        for child in tree.node:
            if isinstance(child, ast.Function) and child.name == function_name:
                self.copyFunction(child, function_node)
                return
        raise TranslationError("function not found: " + function_name, function_node)

    def replaceClassMethods(self, tree, class_name, class_node):
        # find class to replace
        old_class_node = None
        for child in tree.node:
            if isinstance(child, ast.Class) and child.name == class_name:
                old_class_node = child
                break

        if not old_class_node:
            raise TranslationError("class not found: " + class_name, class_node)

        # replace methods
        for function_node in class_node.code:
            if isinstance(function_node, ast.Function):
                found = False
                for child in old_class_node.code:
                    if isinstance(child, ast.Function) and child.name == function_node.name:
                        found = True
                        self.copyFunction(child, function_node)
                        break

                if not found:
                    raise TranslationError("class method not found: " + class_name + "." + function_node.name, function_node)


    def copyFunction(self, target, source):
        target.code = source.code
        target.argnames = source.argnames
        target.defaults = source.defaults
        target.doc = source.doc # @@@ not sure we need to do this any more


    def translateFile(self, module_name, in_file, out_file):
        plat_module = PAT_PLAT_MODULE.match(module_name)
        tree = None
        if plat_module:
            # note that in this case the original module is used by
            # the module translator, becuase it looks it op in modules
            # by the standard module name
            platform, std_module_name = plat_module.groups()[:2]
            if std_module_name:
                module_name = std_module_name
                # if module_name is '' then it is the package of plat
                std_path, std_mod = self.modules[module_name][:2]
                # get the standard module for this override
                std_tree = compiler.parseFile(std_path)
                o_tree = compiler.parseFile(in_file)
                tree = self.merge_ast(std_tree, o_tree)
        if not tree:
            # no overrides or a platform package
            tree = compiler.parseFile(in_file)

        # XXX: src is out of sync if it is an override
        f = file(in_file, "r")
        src = f.read()
        f.close()
        if module_name == self.top_module:
            mn = '__main__'
        else:
            mn = module_name
        t = pyjs.Translator(
            mn, module_name, module_name,
            src, self.debug, tree, out_file, modules=self.modules,
            module_order=self.module_order)

    def translateAll(self):
        for mod in self.module_order:
            module_path, module, g, l = self.modules[mod]
            if not module_path:
                #print "skipping mod without file", mod
                continue
            #print "Translating:", module_path
            out_name = os.path.join(self.js_path, mod)
            out_dir = os.path.dirname(out_name)
            out_file = open(out_name + '.js', 'w')
            self.translateFile(mod, module_path, out_file)
            out_file.close()
            self.js_modules[mod] = out_name + '.js'
            print "Done:", out_name + '.js'

if __name__=='__main__':
    pyjs.path.append('./lib')
    pyjs.path.append('../library')
    pyjs.path.append('../library/builtins')
    js_libs = ['../library/_pyjs.js']
    c = TreeCompiler('simpletest', js_libs=js_libs,
                     platforms=['ms'])
    c.build()
    c.link('ms')
