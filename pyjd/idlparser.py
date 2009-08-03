#!/usr/bin/env python

import sys
import os
import string

class CoClass:
    def __init__(self, uuid, name, f):
        self.uuid = uuid
        self.name = name
        self.f = f
        self.classes = []
        self.parse()

    def pprint(self):
        print self.name, self.uuid
        for fn in self.classes:
            print "\tclass:", fn

    def parse_attribs(self, l):
        l = l[1:-1]
        self.properties = map(string.strip, l.split(','))

    def parse(self):
        while 1:
            l = self.f.readline()
            l = l.strip()
            if l.startswith('}'):
                break
            if l.startswith('['):
                l = l.split(' ')
                self.classes.append(l[-1][:-1])
            elif l.startswith('interface'):
                l = l.split(' ')
                self.classes.append(l[-1][:-1])

class Interface:
    def __init__(self, uuid, name, f):
        self.name = name
        self.uuid = uuid
        self.f = f
        self.props = {}
        self.functions = {}
        self.propput = {}
        self.propget = {}
        self.properties = None

        self.parse()

    def pprint(self):
        print self.name, self.uuid
        for fn in self.functions.keys():
            print "\tfn:", fn
        for fn in self.propput.keys():
            print "\tput:", fn
        for fn in self.propget.keys():
            print "\tget:", fn

    def parse_attribs(self, l):
        l = l[1:-1]
        self.properties = map(string.strip, l.split(','))

    def parse_function(self, l):
        bracket = l.find('(')
        fname = l[8:bracket]

        if self.properties:
            if self.properties[0] == 'propget':
                self.props[fname] = 1
                self.propget[fname] = 1
            elif self.properties[0] == 'propput':
                self.props[fname] = 1
                self.propput[fname] = 1
            else:
                self.functions[fname] = 1

        self.properties = None

    def parse(self):
        while 1:
            l = self.f.readline()
            l = l.strip()
            if l.startswith('}'):
                break
            if l.startswith('['):
                self.parse_attribs(l)
            if l.startswith('HRESULT'):
                self.parse_function(l)

    def cls_print(self, p):
        print "#"*30
        print "# %s" % self.name
        print "#"

        print "class %s(object):" % self.name
        print "\tdef __init__(self, item):"
        print "\t\tself.__dict__['__instance__'] = item"
        print ""

        for p in self.props:
            print "\t#%s" % p
            print "\tdef _get_%s(self):" % p
            print "\t\treturn wrap(self.__instance__.%s)" % p
            print "\tdef _set_%s(self, value):" % p
            print "\t\tself.__instance__.%s = unwrap(value)" % p
            print "\t%s = property(_get_%s, _set_%s)" % (p, p, p)
            print ""

        for f in self.functions:
            print "\t#%s" % f
            print "\tdef %s(self, *args):" % f
            print "\t\targs = map(unwrap, args)"
            print "\t\treturn wrap(self.__instance__.%s(*args))" % f
            print ""

        print "wrapperClasses['%s'] = %s" % (self.uuid, self.name)
        print "backWrapperClasses[%s] = '%s'" % (self.name, self.uuid)
        print

class IdlParser:
    def __init__(self, fname):
        self.f = open(fname, 'r')
        self.interface_order = []
        self.coclass_order = []
        self.interfaces = {}
        self.coclasses = {}
        self.parse()

    def parse_interface(self, line):
        l = line.split(' ')
        interface = l[1]
        if interface.endswith(";"):
            return
        self.interface_order.append(interface)
        self.interfaces[interface] = Interface(self.uuid, interface, self.f)

    def parse_coclass(self, line):
        l = line.split(' ')
        coclass = l[1]
        self.coclass_order.append(coclass)
        self.coclasses[coclass] = CoClass(self.uuid, coclass, self.f)

    def parse_uuid(self, line):
        while 1:
            l = self.f.readline()
            l = l.strip()
            if l.startswith('uuid('):
                self.uuid = '{'+l[5:-1]+'}'
            elif l.startswith(']'):
                return

    def parse(self):
        while 1:
            l = self.f.readline()
            if not l:
                return
            l = l.strip()
            if l.startswith('['):
                self.parse_uuid(l)
            elif l.startswith('interface') or l.startswith('dispinterface'):
                self.parse_interface(l)
            elif l.startswith('coclass'):
                self.parse_coclass(l)
    
if __name__ == '__main__':
    p = IdlParser(sys.argv[1])

    print """\
wrapperClasses = {}
backWrapperClasses = {}
def unwrap(item):
    if item is None:
        return None
    kls = item.__class__
    if not backWrapperClasses.has_key(kls):
        return item
    return item.__instance__
def wrap(item):
    if item is None:
        return None
    kls = item._iid_
    if not wrapperClasses.has_key(kls):
        return item
    return wrapperClasses[kls](item)

"""

    for k in p.interface_order:
        v = p.interfaces[k]
        v.cls_print(p)
    for k, v in p.coclasses.items():
        v.cls_print(p)
