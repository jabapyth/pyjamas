import imputil
import sys
import os
sys.path.append('../')
import pyjs

import cStringIO
import compiler
import types
import shutil
import re
from compiler import ast
import pyjs.treecompiler

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

class SMCompiler(pyjs.treecompiler.TreeCompiler):

    def link(self, platform=None):
        entry_file = self.js_modules[self.top_module]
        f = open(entry_file, 'a')
        print >>f, "//---- initialization --- //"
        for jsf in self.js_libs:
            print >>f, "load('%s');" % jsf
        done = set()
        for mod in self.module_order:
            module = self.modules[mod]
            plat_mod = self.plat_modules[platform].get(mod)
            if plat_mod:
                js_file = self.js_modules[plat_mod.__name__]
            else:
                js_file = self.js_modules[mod]
            if js_file == entry_file:
                continue
            print >>f, "load('%s');" % js_file
        for mod in self.module_order:
            print >>f, '%s();' % mod
        print >>f, "//---- included js_libs --- //"
        # main
        #print >>f, '%s();' % self.top_module
        f.close()


if __name__=='__main__':
    pyjs.path.append(os.path.abspath('./lib'))
    #pyjs.path.append(os.path.abspath('../../client/app'))
    pyjs.path.append(os.path.abspath('../library'))
    pyjs.path.append(os.path.abspath('../library/builtins'))
    js_libs = ['./lib/fixtures.js', '../library/_pyjs.js',
               '../library/sprintf.js']
    c = SMCompiler('simpletest', js_libs=js_libs,
                   platforms=['ms'])
    c.build()
    c.link('ms')
