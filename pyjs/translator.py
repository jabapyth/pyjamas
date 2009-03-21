import ast
import os
import sys
import wrappers
import warnings
import types
from ast import *

LITERALS = {
    'True': 'true',
    'False': 'false',
    'None': 'null'
    }

# This is taken from the django project.
# Escape every ASCII character with a value less than 32.
JS_ESCAPES = (
    ('\'', r'\x27'),
    ('"', r'\x22'),
    ('>', r'\x3E'),
    ('<', r'\x3C'),
    ('&', r'\x26'),
    (';', r'\x3B')
    ) + tuple([('%c' % z, '\\x%02X' % z) for z in range(32)])

def escapejs(value):
    """Hex encodes characters for use in JavaScript strings."""
    for bad, good in JS_ESCAPES:
        value = value.replace(bad, good)
    return value

def translate(py_module, modules, out_file, tree=None, name=None,
              debug_level=0):
    path = os.path.abspath(py_module.__file__)
    if path.endswith('.pyc'):
        path = path[:-1]
    if not tree:
        f = open(path)
        src = f.read()
        f.close()
        tree = ast.parse(src, path)
    #print ast.dump(tree)
    v = Visitor(py_module, modules, name=name, output=out_file,
                debug_level=debug_level)
    v.visit(tree)


undefined = object()

class Visitor(ast.NodeVisitor):

    # counter for temprary names
    tmp_names = 0

    def __init__(self, py_module, modules, name=None,
                 output=sys.stdout, debug_level=0):
        self.globals = py_module.__dict__.copy()
        self.name = self.globals['__name__'] = name or py_module.__name__
        self.locals = {}
        #self.name = py_module.__name__
        self.module = py_module
        self.modules = modules
        self._out = output
        self.ctx = None
        self.defined_globals = set()
        self.debug_level = debug_level
        self.last_exception = None

    def _not_implemented(self, node):
        raise NotImplementedError(
            "%r %s %s:%s" % (dump(node), self.module.__file__,
                             getattr(node,'lineno',None),
                             getattr(node,'col_offset',None)))

    def _js_comment(self, s):
        self._s('/* %s */' % s)

    def visit(self, node):
        if self.debug_level>0:
            if type(node) in (ast.Expr, ast.Assign, ast.Return):
                self._js_comment('line:%s' %getattr(node, 'lineno', None))

        super(Visitor, self).visit(node)

    def flush(self):
        self._out.flush()

    def _l(self, s, ):
        """print to out with newline"""
        self._s(s, suffix='\n')

    def _s(self, s, suffix=' '):
        """print to out with suffix appended"""
        self._out.write(s)
        self._out.write(suffix)

    def _w(self, s):
        """write to out without any whitespace"""
        self._out.write(s)

    # visitors
    def visit_Module(self, node):
        self.ctx = node
        name = self.globals['__name__']
        self._l('//---- start module %s ----//' % name)
        self._s(self.globals['__name__'])
        self._l('= function() {')
        self._l('if(%s.__was_initialized__) {return;};' % name)
        self._l('%s.__was_initialized__=true;' % name)
        self._l(name+ '.__name__ = "%s";' % name)
        self.generic_visit(node)
        self._l('};')
        self._l('//---- end module %s -----//' % name)
        self.ctx = None

    def visit_Import(self, node):
        # | Import(alias* names)
        # alias = (identifier name, identifier? asname)
        # XXX: fixes import order, but is a hack
        for alias in node.names:
            g = self.globals.get(alias.name)
            if not g:
                warnings.warn(
                    "Name of import not found %s" % repr((
                        self.module, dump(node),
                        getattr(node, 'lineno', None))))
                return
            self._l('%s();' % alias.name)

    def visit_ImportFrom(self, node):
        # no op
        pass

    def visit_List(self, node):
        self._s('pyjslib.List([')
        for pos, n in enumerate(node.elts):
            self.visit(n)
            if pos+1<len(node.elts):
                self._s(',')
        self._w('])')

    def visit_Dict(self, node):
        self._s('pyjslib.Dict([')
        for pos, k in enumerate(node.keys):
            v = node.values[pos]
            self._w('[')
            self.visit(k)
            self._s(',')
            self.visit(v)
            self._w(']')
            if pos+1<len(node.keys):
                self._s(',')
        self._w('])')

    def _visit_list(self, iterable, seperator=','):
        if not iterable:
            return
        first = True
        for v in iterable:
            if not first:
                self._s(seperator)
            first = False
            self.visit(v)

    def visit_Discard(self, node):
        raise NotImplementedError

    def visit_Call(self, node):
        # Call(expr func, expr* args, keyword* keywords,
		#	 expr? starargs, expr? kwargs)
        # look if we have the native js func
        if isinstance(node.func, ast.Name):
            name = self._get_name(node.func)
            if name == '__pyjamas__.JS':
                self._l('// start native code %s' % node.lineno)
                self._l(node.args[0].s)
                self._l('// end native code %s' % node.lineno)
                return
        self.visit(node.func)
        self._w('(')
        self._visit_list(node.args)
        self._w(')')

    def visit_Expr(self, node):
        # Expr(expr value)
        if isinstance(node.value, ast.Str):
            # a string expression is documentation so skip it
            return
        self.visit(node.value)
        self._l(';')


    def visit_Subscript(self, node):
        # Subscript(expr value, slice slice, expr_context ctx)
        if type(node.ctx) not in (Load, Del):
            self._not_implemented(node)
        if isinstance(node.slice, ast.Index):
            if isinstance(node.ctx, Load):
                method = '__getitem__'
            elif isinstance(node.ctx, Del):
                method = '__delitem__'
            else:
                self._not_implemented(node)
            # dict or single item lookup
            getitem = ast.Call(
                ast.Attribute(node.value, method, ast.Load()),
                [node.slice.value], [], [], [])
            self.visit(getitem)
            return
        elif isinstance(node.slice, ast.Slice):
            # fields ('lower', 'upper', 'step')
            #Slice(expr? lower, expr? upper, expr? step)
            if node.slice.step:
                self._not_implemented(node)
            # pyjslib.slice(xxx, 1, null)
            lower = node.slice.lower or Name('None', Load())
            upper = node.slice.upper or Name('None', Load())
            getslice = ast.Call(
                ast.Name('pyjslib.slice', ast.Load()),
                [node.value, lower,upper],
                [], [], [])
            self.visit(getslice)
            return
        self._not_implemented(node)


    def visit_Break(self, node):
        self._l('break;')

    def visit_Return(self, node):
        # Return(expr? value)
        self._s('return')
        if node.value is None:
            node.value = Name('None',Load())
        self.visit(node.value)
        self._l(';')

    def visit_Attribute(self, node):
        # we have to check here if we have a class, because attribute
        # acces to classes needs to be done on the prototype
        if isinstance(node.value, ast.Name):
            name = node.value.id
            if name in self.globals:
                g = self.globals.get(name)
                if type(g) is types.ClassType:
                    self._w('%s.__%s.prototype.__class__.%s' %(
                        self.name, g.__name__, node.attr))
                    return
                elif type(g) is types.ModuleType:
                    self._w(name + '.' + node.attr)
                    return
        self.visit(node.value)
        self._w('.' + node.attr)

    def visit_ClassDef(self, node):
        if len(node.bases)>1:
            raise NotImplementedError, node

        n_name = Name(node.name, Load())
        c_name = self._get_name(n_name)
        js_name = '.__'.join(c_name.rsplit('.', 1))
        parent = c_name.split('.', 1)[0]

        # derive from self if no base
        if node.bases:
            base, = node.bases
            # XXX this could be nicer i guess, hm
            if isinstance(base, Attribute):
                g = self.globals.get(base.value.id)
                if not g:
                    self._not_implemented(node)
                b_c_name = base.value.id + '.' + base.attr
            else:
                b_c_name = self._get_name(base)
            b_js_name = '.__'.join(b_c_name.rsplit('.', 1))
        else:
            # XXX hack alarm we need a superclass
            b_js_name = 'pyjslib.__Object'


        # the class object
        self._l(js_name + ' = function () {')
        self._l('var _co = %s' % js_name);
        self._l('var _cls = _co.prototype.__class__');
        self._l('if(_co.__was_initialized__) {return;};')
        self._l('_co.__was_initialized__ = true;')

        ctx = self.ctx
        self.ctx = node

        for n in node.body:
            self.visit(n)
        self.ctx = ctx
        # end of initalization function
        self._l('};')

        # make our object a type
        self._l("pyjs_type('%s', %s, %s, %s)" % (
            node.name, b_js_name, js_name, parent))
        # call the initializer
        self._l(js_name + '();')

    def _method(self, node):
        args = node.args.args
        defaults = node.args.defaults
        if len(defaults)>len(args):
            raise Exception('cannot use self with defaults %s', node.lineno)
        if not isinstance(node.args.args[0], ast.Name):
            raise NotImplementedError, "self attr is no name"

        self.locals[node.name] = node
        # create the private function
        self._s('var %s = function (' % node.name)

        if node.args.kwarg:
            n = Name(node.args.kwarg, Param())
            self._visit_list(args + [n])
        else:
            self._visit_list(args)
        self._l('){')
        self._func_defaults(args, defaults)
        if node.args.vararg:
            self._func_varargs(node, node.args.vararg, len(args))
        old_ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self._l('};')
        self._func_parse_kwargs(node.name, args, defaults)
        self.ctx = old_ctx

        # create the instance method
        self.visit(Name(node.name, Load()))
        self._l(' = pyjs_instancemethod(%s, null, _co);' % node.name)

    def _func_defaults(self, args, defaults):
        # prints out default defs like
        # if (typeof c == 'undefined') c=1;
        for arg, default in zip(reversed(args),
                                reversed(defaults)):
            self._s("if (typeof")
            self.visit(arg)
            self._s(" === 'undefined')")
            self.visit(arg)
            self._s("=")
            self.visit(default)
            self._l(';')

    def _func_parse_kwargs(self, name, args, defaults):
        """generates a default argument parser for a function or mehtod:
        simpletest.__AClass.prototype.getX.parse_kwargs = function ( __kwargs, x, y ) {
        if (typeof x == 'undefined')
            x=__kwargs.x;
        if (typeof y == 'undefined')
            y=__kwargs.y;
         var __r = [x, y];
        return __r;
        };
        """
        if not defaults:
            return
        # we do not want to mess with locals here
        old_locals = self.locals
        self._s(name + '.parse_kwargs =function(__kwargs, ')
        first = True
        self._visit_list(args)

        self._l('){')
        for arg, default in zip(reversed(args),
                                reversed(defaults)):
            self._s('if (typeof')
            self.visit(arg)
            self._s("=== 'undefined')")
            self.visit(arg)
            self._w('=__kwargs.')
            self.visit(arg)
            self._l(';')

        self._s('var __r =[')
        self._visit_list(args)
        self._l('];')
        self._l('return __r;')
        self._l('};')
        self.locals = old_locals

    def _func_varargs(self, node, varargname, start):
        if not varargname:
            return
        self.locals[varargname] = node
        self._l("var %s = pyjslib.List([]);" % varargname)
        self._l("for(var __va_arg=%s ;"
                "__va_arg < arguments.length;"
                "__va_arg++) {" % start)
        self._l("var __arg = arguments[__va_arg];")
        self._l(varargname+".append(__arg);")
        self._l("}")

    def visit_FunctionDef(self, node):
        """sets scopes and dispatches"""
        old_locals = self.locals
        old_d_globals = self.defined_globals
        if isinstance(self.ctx, ast.ClassDef):
            self._method(node)
        elif isinstance(self.ctx, ast.FunctionDef):
            self._function(node)
        elif isinstance(self.ctx, ast.Module):
            self._function(node)
        else:
            raise NotImplementedError, (self.ctx, node, node.lineno)
        self.locals = old_locals
        self.locals[node.name] = node
        self.defined_globals = old_d_globals


    def visit_Lambda(self, node):
        # Lambda(arguments args, expr body)
        old_locals = self.locals
        args = node.args.args
        defaults = node.args.defaults
        self._s('function (){')
        fqn = 'f'
        self._s('var f = function (')
        # add the kwarg argument to the js call
        if node.args.kwarg:
            n = Name(node.args.kwarg, Param())
            self._visit_list(args + [n])
        else:
            self._visit_list(args)
        self._l('){')
        self._func_defaults(args, node.args.defaults)
        if node.args.vararg:
            self._func_varargs(node, node.args.vararg, len(args))
        old_ctx = self.ctx
        self.ctx = node
        self.visit(Return(node.body))
        self._s('};')
        self._func_parse_kwargs(fqn, node.args.args, node.args.defaults)
        self._l('return f;}()')
        self.ctx = old_ctx
        self.locals = old_locals

    def _function(self, node):
        """
        ('name', 'args', 'body', 'decorator_list')
        """
        args = node.args.args
        defaults = node.args.defaults
        self.locals[node.name] = node
        if isinstance(self.ctx, ast.FunctionDef):
            # we are inside a function, so we are local
            self._s('var')
            fqn = node.name
        else:
            fqn = self.name + '.' + node.name
        self._s(fqn + ' = function (')
        # add the kwarg argument to the js call
        if node.args.kwarg:
            n = Name(node.args.kwarg, Param())
            self._visit_list(args + [n])
        else:
            self._visit_list(args)
        self._l('){')
        self._func_defaults(args, node.args.defaults)
        if node.args.vararg:
            self._func_varargs(node, node.args.vararg, len(args))

        old_ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self._l('};')
        self._l("%s.__name__ = '%s';" % (fqn, node.name))
        self._func_parse_kwargs(fqn, node.args.args, node.args.defaults)
        self.ctx = old_ctx


    def visit_Print(self, node):
        # XXX this is ms specific
        self._s('print(')
        self._visit_list(node.values)
        self._l(');')

    def _tmp_name(self, node):
        lineno = getattr(node, 'lineno', None)
        if lineno:
            return '_t%s_%s' % (node.lineno, node.col_offset)
        self.tmp_names += 1
        return '_t%s' % self.tmp_names


    def visit_Assign(self, node):
        # fields: ('targets', 'value')
        if len(node.targets)==1:
            target = node.targets[0]
            if type(target) in (ast.Name, ast.Attribute):
                # we have a simple assignemnt without the need of a local
                # var
                self.visit(target)
                self._s('=')
                self.visit(node.value)
                self._l(';')
                return
            elif isinstance(target, ast.Subscript):
                # we need to call setitem
                if not isinstance(target.slice, ast.Index):
                    self._not_implemented(node)
                setitem = ast.Call(
                    ast.Attribute(target.value, '__setitem__', ast.Load()),
                    [target.slice.value, node.value], [], [], [])
                self.visit(ast.Expr(setitem))
                return

        # we have to create a local var because we must not visit
        # value twice ... it could be intrusive
        tmp = self._tmp_name(node)
        self._s('var %s = ' % tmp)
        self.visit(node.value)
        self._l(';')
        for t in node.targets:
            if isinstance(t, ast.Tuple):
                for i, n in enumerate(t.elts):
                    self.visit(n)
                    self._l('= %s.__getitem__(%s);'% (tmp, i))
            else:
                self.visit(t)
                self._l('=%s;' % tmp)
        # throw away the reference
        self._l('delete %s;' % tmp)

    def visit_Global(self, node):
        self.defined_globals.update(node.names)

    def _get_module(self, name):
        g = self.globals.get(name)
        if not g:
            if name in self.module.__builtins__.keys():
                return 'pyjslib'
            raise LookupError, "Global %s not found" % name
        m = getattr(g,'__module__', self.name)
        # we throw ast classes into globals, so these are module
        # global
        if  m in ('_ast', self.module.__name__):
            m = self.name
        return m

    def _get_name(self, node):
        # look in class, this stays the same
        #print "_get_name", node.id, self.ctx, node.ctx, node.lineno
        if '.' in node.id:
            # we have a js name
            print "Native JS name", node.id
            return node.id
        if node.id in LITERALS:
            if isinstance(node.ctx, ast.Store):
                raise Excpetion('Cannot assign to reserved name')
            return LITERALS[node.id]
        elif isinstance(node.ctx, ast.Param):
            self.locals[node.id] = node
            return node.id
        elif isinstance(self.ctx, ast.Module):
            if isinstance(node.ctx, ast.Store):
                self.globals[node.id] = node
                return self.name + '.' +  node.id
            elif isinstance(node.ctx, ast.Load):
                return self._get_module(node.id) + '.' + node.id
            else:
                raise NotImplementedError
        elif isinstance(self.ctx, ast.FunctionDef) or isinstance(self.ctx, Lambda):
            if isinstance(node.ctx, ast.Store):
                if node.id in self.locals:
                    return node.id
                if node.id in self.defined_globals:
                    return self.name + '.' + node.id
                self.locals[node.id] = node
                return 'var ' + node.id
            elif isinstance(node.ctx, ast.Load):
                if node.id in self.locals:
                    return node.id
                elif node.id in self.globals:
                    return self._get_module(node.id) + '.' + node.id
                elif node.id in self.globals['__builtins__'].keys():
                    # builtins are in pyjslib
                    return 'pyjslib.' + node.id
                else:
                    # is this a javascript?
                    warnings.warn(
                        "Name not found, expecting native %s" % repr((
                            self.module, self.ctx, node.id,
                            getattr(node, 'lineno', None))))
                    return node.id
            else:
                raise NotImplementedError, node
        elif isinstance(self.ctx, ast.ClassDef):
            if isinstance(node.ctx, Store) or node.id in self.locals:
                return '_cls.%s' %  node.id;
            else:
                return self._get_module(node.id) + '.' + node.id
        raise NotImplementedError, (node.id, self.ctx, node.ctx)

    def visit_Name(self, node):
        self._w(self._get_name(node))

    def visit_Const(self, node):
        raise NotImplementedError, node

    def visit_Num(self, node):
        self._w(str(node.n))

    def visit_Pass(self, node):
        pass

    def visit_Not(self, node):
        self._s('!')

    def _visit_multicompare(self, node):
        # XXX:this does not work in assignemnents, we have to create a
        # js method
        return
        name_nodes = []
        for n in [node.left] + node.comparators:
            name = Name(self._tmp_name(n), Store())
            name_nodes.append(name)
            self.visit(Assign(targets=[name], value=n))
        b_node = BoolOp(op=And(), values=[])
        for i, n in enumerate(name_nodes):
            if i+1==len(name_nodes):
                break
            n.ctx = Load()
            c_node = Compare(left=n,
                             ops=[node.ops[i]],
                             comparators=[name_nodes[i+1]])
            b_node.values.append(c_node)
        self.visit(b_node)


    def visit_Compare(self, node):
        # | Compare(expr left, cmpop* ops, expr* comparators)
        if len(node.comparators)>1:
            self._not_implemented(node)
        op = node.ops[0]
        c = node.comparators[0]
        if type(op) in (ast.In, ast.NotIn):
            if isinstance(op, ast.NotIn):
                self._s('!')
            expr = ast.Call(
                ast.Attribute(c, '__contains__', ast.Load()),
                [node.left], [], [], [])
            self.visit(expr)
            return
        self.visit(node.left)
        self.visit(op)
        self.visit(c)

    def visit_Str(self, node):
        self._w("'" + escapejs(node.s) + "'")

    def _test_bool(self, testnode):
        # makes a test that always a bool is returned
        if isinstance(testnode, Name) and testnode.id in ('True', 'False'):
            self.visit(testnode)
        elif type(testnode) not in (Compare, Num):
            # amke truth testing with the bool func
            self._s('pyjslib.bool(')
            self.visit(testnode)
            self._s(')')
        else:
            self.visit(testnode)



    def visit_While(self, node):
        # While(expr test, stmt* body, stmt* orelse)

        #         while (pyjslib.bool(true)) {
        #             i += 1;
        #             pyjslib.printFunc([ i ], 1 );
        #             if (pyjslib.bool((i > 3))) {
        #                 break;
        #                 }

        self._s('while (')
        self._test_bool(node.test)
        self._l(') {')
        for n in node.body:
            self.visit(n)
        self._s('}')
        if node.orelse:
            self._not_implemented(node)


    def visit_If(self, node):
        self._s('if (')
        self._test_bool(node.test)
        self._l(') {')
        for n in node.body:
            self.visit(n)
        self._s('}')
        if node.orelse:
            self._l('else {')
            for n in node.orelse:
                self.visit(n)
            self._l('}')


    def visit_Tuple(self, node):
        # fields: ('elts', 'ctx')
        if isinstance(node.ctx, ast.Store):
            raise NotImplementedError, (node, node.ctx, node.elts, node.lineno)
        elif not isinstance(node.ctx, ast.Load):
            raise NotImplementedError, (node, node.ctx, node.elts, node.lineno)

        self._s('pyjslib.Tuple([')
        self._visit_list(node.elts)
        self._s("])")

    def visit_AugAssign(self, node):
        # AugAssign(expr target, operator op, expr value)
        self.visit(node.target)
        self.visit(node.op)
        self._s('=')
        self.visit(node.value)
        self._l(';')

    def visit_ListComp(self, node):
        # ListComp(expr elt, comprehension* generators)
        # comprehension = (expr target, expr iter, expr* ifs)
        if not len(node.generators)==1:
            self._not_implemented(node)
        generator  = node.generators[0]
        if len(generator.ifs)>1:
            self._not_implemented(node)

        self._s('function(){')
        tmp_name = Name(self._tmp_name(node), Store())

        a = Assign(targets=[tmp_name],
                    value=List(elts=[], ctx=Load()))
        self.visit(a)
        tmp_name.ctx = Load()

        append = Expr(value=Call(func=Attribute(value=tmp_name,
                                                attr='append', ctx=Load()),
                                args=[Name(id=generator.target.id, ctx=Load())],
                     keywords=[], starargs=None, kwargs=None))
        if generator.ifs:
            body = [If(test=generator.ifs[0], body=[append], orelse=[])]
        else:
            body = [append]

        f = For(target=generator.target,
                iter=generator.iter,
                body=body, orelse=[])

        self.visit(f)
        self.visit(Return(value=tmp_name))
        self._s('}()')

    def visit_For(self, node):
        #('target', 'iter', 'body', 'orelse')
        if node.orelse:
            raise NotImplementedError, (node, node.lineno)
        iter_name = Name(self._tmp_name(node), Store())
        # assignement to tmp
        assign_iter = Assign(targets=[iter_name],
                             value=Call(
                                 func=Attribute(value=node.iter,
                                                attr='__iter__', ctx=Load()),
                          args=[], keywords=[], starargs=None, kwargs=None))
        self.visit(assign_iter)
        # setting iterator context to load
        iter_name.ctx = Load()
        # the while loop
        w = While(test=Name(id='True', ctx=Load()), body=[
            TryExcept(body=[
                Assign(targets=[node.target],
                       value=Call(
                           func=Attribute(
                               value=iter_name, attr='next',
                               ctx=Load()), args=[], keywords=[],
                           starargs=None, kwargs=None))] + node.body,
                handlers=[ExceptHandler(
                          type=Name(id='StopIteration', ctx=Load()),
                          name=None, body=[Break()])],
                      orelse=[Raise(type=None, inst=None, tback=None)])], orelse=[])
        self.visit(w)

    def visit_Delete(self, node):
        # Delete(expr* targets)
        for node in node.targets:
            self._s('delete')
            self.visit(node)
            self._l(';')


    # comparison operators
    def visit_Eq(self, node):
        self._s('===')
    # XXX: this is not an identity check
    visit_Is = visit_Eq
    def visit_NotEq(self, node):
        self._s('!==')
    # XXX: this is not an identity check
    visit_IsNot = visit_NotEq

    def visit_Lt(self, node):
        self._s('<')
    def visit_LtE(self, node):
        self._s('<=')
    def visit_Gt(self, node):
        self._s('>')
    def visit_GtE(self, node):
        self._s('>=')

    visit_In = _not_implemented # should be catched in compare
    visit_NotIn = _not_implemented # should be catched in compare

    # operators
    def visit_Add(self, node):
        self._w('+')
    def visit_Sub(self, node):
        self._w('-')
    def visit_Mult(self, node):
        self._w('*')
    def visit_Div(self, node):
        self._w('/')
    def visit_Mod(self, node):
        # we should never get here if we need sprintf, this has to be
        # decided at runtime
        print "XXX", node, getattr(node,'lineno',None)
        self._w('%')
    def visit_BitAnd(self, node):
        self._w('&')
    def visit_BitOr(self, node):
        self._w('|')
    def visit_LShift(self, node):
        self._w('<<')
    def visit_RShift(self, node):
        self._w('>>>')
    def visit_BitXor(self, node):
        self._w('^')

    def visit_BoolOp(self,node):
        self._w('(')
        first = True
        for v in node.values:
            if not first:
                self.visit(node.op)
            self._w('(')
            first = False
            self.visit(v)
            self._w(')')

        self._w(')')

    def visit_And(self, body):
        self._w('&&')

    def visit_Or(self, body):
        self._w('||')

    def visit_Raise(self, node):
        # Raise(expr? type, expr? inst, expr? tback)
        if node.tback:
            self._not_implemented(node)
        if not node.type:
            if not self.last_exception:
                self._not_implemented(node)
            nt = Name(self.last_exception, Param())
        else:
            nt = node.type
        self._w('throw(')
        if node.inst:
            expr = Call(func=nt,
                        args=[node.inst], keywords=[],
                        starargs=None, kwargs=None)
        else:
            expr = nt
        self.visit(expr)
        self._l(');')

    def visit_TryFinally(self, node):
        # TryFinally(stmt* body, stmt* finalbody)
        self._l('try{')
        for n in node.body:
            self.visit(n)
        self._l('} finally {')
        for n in node.finalbody:
            self.visit(n)
        self._l('};')

    visit_ExceptHandler = _not_implemented

    def visit_TryExcept(self, node):
        # TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
        self._l('try{')
        for n in node.body:
            self.visit(n)
        err_name = self._tmp_name(node)
        
        self._w('}catch(%s){' % err_name)
        # we have to set the tmp error name to param context, so it
        # always is local, even in module context
        n_err_name = Name(err_name, Param())
        self.last_exception = err_name
        def _hexpr_test(handler):
            if not handler.type:
                return Name('True', Load())
            return BoolOp(op=Or(),
                          values=[Compare(left=n_err_name,  ops=[Eq()],
                                comparators=[handler.type]),
                            Call(func=Name(id='isinstance', ctx=Load()),
                                args=[n_err_name, handler.type],
                                 keywords=[], starargs=None, kwargs=None)])

        current_if = top_if = None
        for handler in node.handlers:
            # XXX: improve this, the if is not needed
            if handler.name:
                body = [Assign(targets=[handler.name],
                               value=n_err_name)] + handler.body
            else:
                body = handler.body
            stmt = If(test=_hexpr_test(handler), body=body, orelse=[])
            if current_if:
                current_if.orelse.append(stmt)
                print current_if.orelse
            else:
                top_if = stmt
            current_if = stmt
        if node.orelse:
            top_if.orelse.extend(node.orelse)
        else:
            top_if.orelse.append(
                Raise(type=n_err_name, inst=None, tback=None))
        self.visit(top_if)
        self._l('}')
        self.last_exception = None

    def visit_BinOp(self, node):
        # BinOp(expr left, operator op, expr right)
        if isinstance(node.op, Pow):
            n = Call(func=Name(id='Math.pow', ctx=Load()),
                     args=[node.left, node.right],
                     keywords=[], starargs=None, kwargs=None)
            self.visit(n)
        else:
            self.generic_visit(node)

    def visit_UnaryOp(self, node):
        # UnaryOp(unaryop op, expr operand)
        print dump(node), node.lineno
        if type(node.op) in (Not,):
            self.visit(node.op)
            self._test_bool(node.operand)
        else:
            self.generic_visit(node)


    def visit_Pow(self, node):
        # we should never get here
        self._not_implemented(node)


    visit_FloorDiv = _not_implemented
    # not implemented expressions

    # visit_UnaryOp = _not_implemented not needed (not tested for all ops)

    visit_IfExp = _not_implemented
    visit_IfExp = _not_implemented
    visit_GeneratorExp = _not_implemented
    visit_Yield = _not_implemented
    visit_Repr = _not_implemented
    #-- the following expression can appear in assignment context


    # not implemented statements
    visit_With = _not_implemented

    visit_Assert = _not_implemented
    visit_Exec = _not_implemented
    visit_Continue = _not_implemented
