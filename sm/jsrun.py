#!/usr/bin/env python

import sys
import os
from optparse import OptionParser
import subprocess
import shutil

here = os.path.dirname(os.path.abspath(__file__))

template = """
// make basic stuff work 
$wnd = {};
$doc = {};
$wnd.location = {};
window = $wnd;
$wnd.location.hash = 'fakehasch';
$wnd.addEventListener = function(){};
$wnd.__pygwt_initHandlers = function(){};
$wnd.setTimeout = function(){};

defaultStatus = null;
alert = print;


pyjamas = function () {
pyjamas.__name__ = 'pyjamas';
}


//---------aplibs------------
%(app_libs)s

//-----------module----------
%(module)s
"""

def main():
    import pyjs
    parser = OptionParser(
        usage="usage: %s [options] path" % sys.argv[0])
    parser.add_option("-o", "--output",
                      default=os.path.abspath('output'),
                      help="pyjs compiler output directory"
                            "default %default",
                      dest="output")
    options, args = parser.parse_args()
    pattern = None
    if len(args)<1:
        parser.error('No path given')
        sys.exit(1)
    path = os.path.abspath(args[0])
    if not os.path.isfile(path):
        parser.error('No such file %s' % test_dir)
        sys.exit(1)
    run(path, options.output)

def run(path, output='output', debug=False):
    file_dir, file_name = os.path.split(path)
    module_name = file_name[:-3]
    import pyjs
    if not file_dir in pyjs.path:
        pyjs.path.insert(0, file_dir)
    from pprint import pprint
    print "-"*80
    for name, path in pyjs.gatherDeps(path):
        print name, path
    print "-"*80
    return
    output = os.path.abspath(output)
    if os.path.exists(output):
        shutil.rmtree(output)
    os.mkdir(output)


    
    parser = pyjs.PlatformParser(here)
    parser.setPlatform("spidermonkey")

    print "Compiling JS"
    print "-"*80
    app_translator = pyjs.AppTranslator(parser=parser)
    app_libs, app_code = app_translator.translate(
        module_name, debug=debug,
        library_modules=['_pyjs.js', 'sys', 'pyjslib'])

    file_contents = template % {'app_libs': app_libs, 'module_name': module_name,
                      'module': app_code}

    done = set()
    for mod_name in reversed(app_translator.library_modules):
        for ns in pyjs.subdeps(mod_name):
            print "------------", ns
            file_contents += "%s();\n" % ns

    out_path = os.path.join(output, '%s.js' % module_name)
    f = open(out_path, 'w')
    f.write(file_contents)
    f.close()
    js = subprocess.Popen(['js %s' % out_path],
                          shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    print "Running JS"
    print "-"*80

    o,e = js.communicate()
    if e:
        print "-"*80
        print >> sys.stderr, "JS Exception in: ", out_path
        print >> sys.stderr, e
        path, lineno, err_name, err_msg = e.split(':', 3)
        src = open(path)
        curr_line = 0
        lineno = int(lineno)
        for line in src:
            curr_line += 1
            if curr_line == lineno:
                print >> sys.stderr, '>', curr_line, line,
            elif curr_line > lineno-10:
                print >> sys.stderr, ' ', curr_line, line,
            if curr_line > lineno+4:
                sys.exit(1)
    print "JS Output"
    print "-"*80
    print o


if __name__ == '__main__':
    pj_root = os.path.dirname(here)
    sys.path.append(os.path.join(pj_root, "pyjs"))
    import pyjs
    for p in ("library/builtins",
              "library",
              "addons"):
        pyjs.path.append(os.path.join(pj_root, p))
    main()
