import imputil
import sys
import pyjs
import translator
import os
import cStringIO
import compiler
import types
import shutil
import re
#from compiler import ast
import ast

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

    def _import_hook(self, fqname, globals=None, locals=None, fromlist=None):
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
            self._modules[fqname] = m
            self._order.append(fqname)

    def getModules(self):
        return self._order, self._modules

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
        #print pyjs.path
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
        mgr = ImportManager()
        sys.modules = {}
        self._import(self.top_module, mgr)
        import_order, self.modules = mgr.getModules()
        self.module_order = []
        # get the packages first
        packages = []
        for m in import_order:
            subs = [s for s in import_order if s.startswith(m +'.')]
            for sub in subs:
                packages.append(m)
                break

        self.module_order=sorted(packages, key=lambda x: len(x.split('.')))
        for m in reversed(import_order):
            if m in self.module_order:
                continue
            self.module_order.append(m)
        # XXX: hack put pyjslib first, we have to do something linke
        # builtins
        if 'pyjslib' in self.module_order:
            self.module_order.remove('pyjslib')
            self.module_order.insert(0, 'pyjslib')

        # import the platform modules
        for plat in self.platforms:
            self.plat_modules[plat] = {}
            for mod in self.module_order:
                if mod == 'sys':
                    continue
                pmod = '__plat_%s__.%s' % (plat, mod)
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
                if ms:
                    self.plat_modules[plat][mod] = ms[-1]


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
        raise NotImplementedError("Needs to be implemented in subclass")

    def _modulePath(self, m):
        """returns the python file for module"""
        f = getattr(m,'__file__', None)
        if f:
            f = os.path.abspath(f)
            if f.endswith('.pyc'):
                f = f[:-1]
        return f

    def translateModule(self, module_name):
        """translates the module and its overrides to js"""
        module = self.modules[module_name]
        path = self._modulePath(module)
        if not path:
            print "skipping module without path", module
        tree = compiler.parseFile(path)
        # XXX: src is out of sync in platforms
        f = file(path, "r")
        src = f.read()
        f.close()
        if module_name == self.top_module:
            mn = '__main__'
        else:
            mn = module_name
        out_name = os.path.join(self.js_path, module_name)
        out_file = open(out_name + '.js', 'w')
        translator.translate(module, self.modules, out_file,
                             name=mn)
#         t = pyjs.Translator(
#             mn, module_name, module_name,
#             src, self.debug, tree, out_file, modules=self.modules,
#             module_order=self.module_order)
        out_file.close()
        print out_name
        self.js_modules[module_name] = out_name + '.js'
        for plat in self.platforms:
            plat_module = self.plat_modules[plat].get(module_name)
            if not plat_module:
                continue
            plat_path = self._modulePath(plat_module)
            if not plat_path:
                print "skipping platform module without path", plat_module
                continue
            ptree = compiler.parseFile(plat_path)
            # XXX is the tree modified?
            import pdb;pdb.set_trace()
            mtree = self.merge_ast(tree, ptree)
            out_name = os.path.join(self.js_path, plat_module.__name__)
            out_file = open(out_name + '.js', 'w')
            # XXX enable this again, when the merge stuff is done
#             t = pyjs.Translator(
#                 mn, module_name, module_name,
#                 src, self.debug, mtree, out_file, modules=self.modules,
#                 module_order=self.module_order)
            out_file.close()
            self.js_modules[plat_module.__name__] = out_name + '.js'

    def translateAll(self):
        for mod in self.module_order:
            self.translateModule(mod)
        return

