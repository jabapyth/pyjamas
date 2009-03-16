import sys

def importModule(fqname):
    """returns a list of modules needed to import fqname"""
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

print importModule('pyjslib')
print importModule('__plat_ms__.pyjslib')
print importModule('pyjamas.ui.Label')

