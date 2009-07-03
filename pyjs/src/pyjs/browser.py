import os
from pyjs import linker
from pyjs import translator
from pyjs import util
from cStringIO import StringIO
from optparse import OptionParser
import pyjs

AVAILABLE_PLATFORMS = ('IE6', 'Opera', 'OldMoz', 'Safari', 'Mozilla')

BOILERPLATE_PATH = os.path.join(os.path.dirname(__file__), 'boilerplate')

APP_HTML_TEMPLATE = """\
<html>
<!-- auto-generated html - you should consider editing and
adapting this to suit your requirements
-->
<head>
<meta name="pygwt:module" content="%(modulename)s">
%(css)s
<title>%(title)s</title>
</head>
<body bgcolor="white">
<script language="javascript" src="bootstrap.js"></script>
</body>
</html>
"""

class BrowserLinker(linker.BaseLinker):

    def visit_start(self):
        self.boilerplate_path = None
        self.js_libs.append('_pyjs.js')
        self.js_libs.append('sprintf.js')
        if not os.path.exists(self.output):
            os.makedirs(self.output)
        self.merged_public = set()
        self.visited_modules = {}

    def visit_module(self, module_path, overrides, platform,
                     module_name):
        # look if we have a public dir
        dir_name = os.path.dirname(module_path)
        if not dir_name in self.merged_public:
            public_folder = os.path.join(dir_name, 'public')
            if os.path.exists(public_folder) and os.path.isdir(public_folder):
                util.copytree_exists(public_folder,
                                     self.output)
                self.merged_public.add(dir_name)
        if platform and overrides:
            out_file = '%s.__%s__.js' % (module_path[:-3], platform)
        else:
            out_file = '%s.js' % module_path[:-3]
        if out_file in self.done.get(platform, []):
            return
        if platform is None:
            deps = translator.translate([module_path] +  overrides,
                                        out_file,
                                        module_name=module_name,
                                        **self.translator_arguments)
            self.dependencies[out_file] = deps
            if '.' in module_name:
                for i, dep in enumerate(deps):
                    if linker.module_path(dep, path=[dir_name]):
                        deps[i] = '.'.join(module_name.split('.')[:-1] + [dep])
        else:
            deps = self.dependencies[out_file]
        if out_file not in self.done.setdefault(platform, []):
            self.done[platform].append(out_file)
        if module_name not in self.visited_modules.setdefault(platform, []):
            self.visited_modules[platform].append(module_name)
        if deps:
            self.visit_modules(deps, platform)

    def visit_end_platform(self, platform):
        if not platform:
            return
        self._generate_app_file(platform)

    def visit_end(self):
        html_output_filename = os.path.join(self.output, self.top_module + '.html')
        if not os.path.exists(html_output_filename):
            # autogenerate
            self._create_app_html(html_output_filename)
        self._create_nocache_html()

    def find_boilerplate(self, name):
        if not self.boilerplate_path:
            self.boilerplate_path = [BOILERPLATE_PATH]
            module_bp_path = os.path.join(
                os.path.dirname(self.top_module_path), 'boilerplate')
            if os.path.isdir(module_bp_path):
                self.boilerplate_path.insert(0, module_bp_path)
        for p in self.boilerplate_path:
            bp =  os.path.join(p, name)
            if os.path.exists(bp):
                return bp
        raise RuntimeError("Boilerplate not found %r" % name)

    def read_boilerplate(self, name):
        f = file(self.find_boilerplate(name))
        res = f.read()
        f.close()
        return res

    def _generate_app_file(self, platform):
        # TODO: cache busting
        template = self.read_boilerplate('all.cache.html')
        out_path = os.path.join(
            self.output,
            '.'.join((self.top_module, platform, 'cache.html')))
        app_code = StringIO()
        done = self.done[platform]
        for p in done:
            f = file(p)
            app_code.write(f.read())
            f.close()
        scripts = ['<script type="text/javascript" src="%s"></script>'%script \
                   for script in self.js_libs]
        app_body = '\n'.join(scripts)
        deps = []
        file_contents = template % dict(
            app_name = self.top_module,
            early_app_libs = '',
            app_libs = app_code.getvalue(),
            app_body = app_body,
            platform = platform.lower(),
            available_modules = self.visited_modules[platform],
            dynamic = 0,
            app_headers = ''
        )
        out_file = file(out_path, 'w')
        out_file.write(file_contents)
        out_file.close()

    def _create_nocache_html(self):
        # nocache
        template = self.read_boilerplate('home.nocache.html')
        out_path = os.path.join(self.output, self.top_module + ".nocache.html")
        select_tmpl = """O(["true","%%s"],"%s.%%s.cache.html");\n""" % self.top_module
        script_selectors = StringIO()
        for platform in self.platforms:
            script_selectors.write(
                select_tmpl % (platform, platform))
        out_file = file(out_path, 'w')
        out_file.write(template % dict(
            app_name = self.top_module,
            script_selectors = script_selectors.getvalue()
            ))
        out_file.close()

    def _create_app_html(self, file_name):
        """ Checks if a base HTML-file is available in the PyJamas
        output directory.
        If the HTML-file isn't available, it will be created.

        If a CSS-file with the same name is available
        in the output directory, a reference to this CSS-file
        is included.

        If no CSS-file is found, this function will look for a special
        CSS-file in the output directory, with the name
        "pyjamas_default.css", and if found it will be referenced
        in the generated HTML-file.
        """

        # if html file in output directory exists, leave it alone.
        if os.path.exists(file_name):
            return 0
        if os.path.exists(
            os.path.join(self.output, self.top_module + '.css' )):
            css = "<link rel='stylesheet' href='" + self.top_module + ".css'>"
        elif os.path.exists(
            os.path.join(self.output, 'pyjamas_default.css' )):
            css = "<link rel='stylesheet' href='pyjamas_default.css'>"
        else:
            css = ''

        title = 'PyJamas Auto-Generated HTML file ' + self.top_module

        base_html = APP_HTML_TEMPLATE % {'modulename': self.top_module,
                                         'title': title, 'css': css}

        fh = open (file_name, 'w')
        fh.write  (base_html)
        fh.close  ()
        return 1

def build_script():
    usage = """
    usage: %prog [options] <application module name>

    This is the command line builder for the pyjamas project, which can
    be used to build Ajax applications from Python.
    For more information, see the website at http://pyjs.org/
    """
    global app_platforms
    parser = OptionParser(usage = usage)
    # TODO: compile options
    #pyjs.add_compile_options(parser)
    parser.add_option("-o", "--output", dest="output",
        help="directory to which the webapp should be written")
    parser.add_option("-j", "--include-js", dest="js_includes", action="append",
        help="javascripts to load into the same frame as the rest of the script")
    parser.add_option("-I", "--library_dir", dest="library_dirs",
        action="append", help="additional paths appended to PYJSPATH")
    parser.add_option("-P", "--platforms", dest="platforms",
        help="platforms to build for, comma-separated")

    parser.set_defaults(output="output",
                        js_includes=[],
                        library_dirs=[],
                        platforms=(','.join(AVAILABLE_PLATFORMS))
                        )
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    top_module = args[0]
    for d in options.library_dirs:
        pyjs.path.append(os.path.abspath(d))

    if options.platforms:
       app_platforms = options.platforms.lower().split(',')
    print pyjs.path

    translator_arguments=dict(debug=False,
                              print_statements = True,
                              function_argument_checking=True,
                              attribute_checking=True,
                              source_tracking=False,
                              line_tracking=False,
                              store_source=False)
    l = BrowserLinker(top_module,
                      output=options.output,
                      platforms=app_platforms,
                      path=pyjs.path,
                      translator_arguments=translator_arguments)
    l()
