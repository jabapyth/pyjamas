import ast
import os
import sys
import wrappers
import warnings
import types

LITERALS = {
    'True': 'true',
    'False': 'false',
    'None': 'null'
    }


def translate(py_module, modules, out_file, tree=None, name=None):
    path = os.path.abspath(py_module.__file__)
    if path.endswith('.pyc'):
        path = path[:-1]
    if not tree:
        f = open(path)
        src = f.read()
        f.close()
        tree = ast.parse(src, path)
    #print ast.dump(tree)
    v = Visitor(py_module, modules, name=name, output=out_file)
    v.visit(tree)


undefined = object()

class Visitor(ast.NodeVisitor):

    # counter for temprary names
    tmp_names = 0

    def __init__(self, py_module, modules, name=None,
                 output=sys.stdout):
        self.globals = py_module.__dict__.copy()
        self.name = self.globals['__name__'] = name or py_module.__name__
        self.locals = {}
        #self.name = py_module.__name__
        self.module = py_module
        self.modules = modules
        self._out = output
        self.ctx = None
        self.self_name = None
        self.defined_globals = set()

    def _not_implemented(self, node):
        raise NotImplementedError(
            "%r %s %s:%s" % (node, self.module.__file__,
                             getattr(node,'lineno',None),
                             getattr(node,'col_offset',None)))

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
        self._l(name+ '.__name__ = "%s";' % name)
        self.generic_visit(node)
        self._l('};')
        self._l('//---- end module %s -----//' % name)
        self.ctx = None

    def visit_Import(self, node):
        # no op
        pass
    def visit_ImportFrom(self, node):
        # no op
        pass

    def visit_List(self, node):
        self._s('new pyjslib.List([')
        for pos, n in enumerate(node.elts):
            self.visit(n)
            if pos+1<len(node.elts):
                self._s(',')
        self._w('])')

    def visit_Dict(self, node):
        self._s('new pyjslib.Dict([')
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

        if node.starargs:
            raise NotImplementedError
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
        self._s(')')

    def visit_Expr(self, node):
        # Expr(expr value)
        if isinstance(node.value, ast.Str):
            # a string expression is documentation so skip it
            return
        self.visit(node.value)
        self._l(';')

    def visit_Subscript(self, node):
        # Subscript(expr value, slice slice, expr_context ctx)
        if not isinstance(node.ctx, ast.Load):
            self._not_implemented(node)
        if isinstance(node.slice, ast.Index):
            method = '__getitem__'
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
            getslice = ast.Call(
                ast.Name('pyjslib.slice', ast.Load()),
                [node.value, node.slice.lower, node.slice.upper],
                [], [], [])
            self.visit(getslice)
            return
        self._not_implemented(node)


    def visit_Break(self, node):
        self._l('break;')

    def visit_Return(self, node):
        self._s('return')
        self.visit(node.value)
        self._l(';')

    def visit_Attribute(self, node):
        # we have to check here if we have a class, because attribute
        # acces to classes needs to be done on the prototype
        #                         g = self.globals[node.id]
        #                 m = self._get_module(node.id)
        #                 if node.id=='A':
        #                     import pdb;pdb.set_trace()
        #                 if type(g) is types.ClassType:
        #                     return '%s.__%s.prototype.__class__.%s' %(
        #                         m, g.__name__, node.id)
        #    simpletest.__A.prototype.__class__.l.append(1000);
        if isinstance(node.value, ast.Name):
            name = node.value.id
            if name in self.globals:
                g = self.globals.get(name)
                if type(g) is types.ClassType:
                    self._w('%s.__%s.prototype.__class__.%s' %(
                        self.name, g.__name__, node.attr))
                    return
        #import pdb;pdb.set_trace()
        self.visit(node.value)
        self._w('.' + node.attr)

    def visit_ClassDef(self, node):
        if len(node.bases)>1:
            raise NotImplementedError, node

        # get the python object wrapper
        klass = wrappers.getWrapper(self.globals[node.name])
        # the class object
        js_name = self.name + '.__' + node.name
        c_name = self.name + '.' + node.name
        self._l(js_name + ' = function () {};')

        # the constructor
        self._l(c_name + ' = function () {')
        self._l("var instance = new " + js_name + "();")
        self._l("if (instance.__init__) "
                "{instance.__init__.apply(instance, arguments)};")
        self._l("return instance;")
        self._l("};")

        # set the name
        self._l(c_name + '.__name__ = "' + node.name + '";')

        # initializer
        init_name = js_name + '_initialize'
        self._l(init_name + ' = function() {')
        self._l('if(%s.__was_initialized__) {return;};' % js_name)
        self._l('%s.__was_initialized__ = true;' % js_name)
        # TODO: bases
        #self._l('if(%s.__was_initialized__) {return;};' % js_name)

        # derive from self if no base
        if klass.base:
            self._s("if(!"+klass.base.js_name+".__was_initialized__) {")
            self._l(klass.base.js_name+"_initialize();};")
            self._l("pyjs_extend(" + js_name + ", "+ klass.base.js_name + ");")
        else: # XXX hack alarm we need a superclass
            self._s("if(!"+js_name+".__was_initialized__) {")
            self._l(js_name+"_initialize();};")
            self._l("pyjs_extend(" + js_name + ", "+ js_name + ");")

        ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self.ctx = ctx
        proto_name = '%s.__%s.prototype.__class__' % (self.name, node.name)
        self._l('%s.__new__ =  %s;' % (proto_name, c_name))
        self._l('%s.__name__ =  "%s";' % (proto_name, node.name))
        self._l('};')
        self._l(js_name+"_initialize();")

    def _method(self, node):
        args = node.args.args[1:]
        defaults = node.args.defaults
        if len(defaults)>len(args):
            raise Exception('cannot use self with defaults %s', node.lineno)
        if not isinstance(node.args.args[0], ast.Name):
            raise NotImplementedError, "self attr is no name"
        self.self_name = node.args.args[0].id
        fqn = '%s.__%s.prototype.__class__.%s' % (self.name, self.ctx.name,
                                                  node.name)
        self._s(fqn + ' = function (')
        self._visit_list(args)
        if node.args.kwarg:
            self.locals[node.args.kwarg] = node
            self._w(', %s' % node.args.kwarg)
        self._l('){')
        self._func_defaults(args, defaults)
        if node.args.vararg:
            self._func_varargs(node, node.args.vararg, len(args))
        old_ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self._l('};')
        self._func_parse_kwargs(fqn, args, defaults)
        self.ctx = old_ctx

        js_i_name =  '%s.__%s.prototype.%s' % (self.name, self.ctx.name,
                                               node.name)
        self._l(fqn + '.unbound_method = true;')

        self._l(fqn + ".__name__ = '%s';" % node.name)
        self._l(js_i_name + ".__name__ = '%s';" % node.name)
        self._l(js_i_name + '.instance_method = true;')

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
        self._l("var %s = new new pyjslib.List([]);" % varargname)
        self._l("for(var __va_arg=%s ;"
                "__va_arg < arguments.length;"
                "__va_arg++) {" % start)
        self._l("var __arg = arguments[__va_arg];")
        self._l(varargname+".append(__arg);")
        self._l("}")

    def visit_FunctionDef(self, node):
        """sets scopes and dispatches"""
        old_locals = self.locals
        old_self = self.self_name
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
        self.self_name = old_self
        self.defined_globals = old_d_globals


    def _function(self, node):
        """
        ('name', 'args', 'body', 'decorator_list')
        """
        self.self_name = None

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
        self._visit_list(args)
        if node.args.kwarg:
            self.locals[node.args.kwarg] = node
            self._w(', %s' % node.args.kwarg)
        self._l('){')
        self._func_defaults(args, node.args.defaults)
        if node.args.vararg:
            self._func_varargs(node, node.args.vararg, len(args))

        old_ctx = self.ctx
        self.ctx = node
        for n in node.body:
            self.visit(n)
        self._l('};')
        self._l("%s.__name__ = '%s'" % (fqn, node.name))
        self._func_parse_kwargs(fqn, node.args.args, node.args.defaults)
        self.ctx = old_ctx


    def visit_Print(self, node):
        # XXX this is ms specific
        self._s('print(')
        for n in node.values:
            self.visit(n)
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
        m = getattr(self.globals[name],
                    '__module__', self.name)
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
        elif isinstance(self.ctx, ast.FunctionDef):
            if node.id == self.self_name:
                return 'this'
            if isinstance(node.ctx, ast.Store):
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
                            self.module, self.ctx, node.id, node.lineno)))
                    return node.id
            else:
                raise NotImplementedError, node
        elif isinstance(self.ctx, ast.ClassDef):
            return '.'.join((self.name,
                             '__' +  self.ctx.name,
                             'prototype',
                             '__class__',
                             node.id))
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

    def visit_Compare(self, node):
        if len(node.comparators)>1:
            raise NotImplementedError
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
        self._w("'" + node.s + "'")

    def _test_bool(self, testnode):
        # makes a test that always a bool is returned
        if not isinstance(testnode, ast.Compare):
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
        for n in node.orelse:
            self._s('else')
            is_else = not isinstance(n, ast.If)
            if is_else: # this is the last else
                self._l('{')
            self.visit(n)
            if is_else: # this is the last else
                self._s('}')


    def visit_If(self, node):
        self._s('if (')
        self._test_bool(node.test)
        self._l(') {')
        for n in node.body:
            self.visit(n)
        self._s('}')
        for n in node.orelse:
            self._s('else')
            is_else = not isinstance(n, ast.If)
            if is_else: # this is the last else
                self._l('{')
            self.visit(n)
            if is_else: # this is the last else
                self._s('}')


    def visit_Tuple(self, node):
        # fields: ('elts', 'ctx')
        if isinstance(node.ctx, ast.Store):
            raise NotImplementedError, (node, node.ctx, node.elts, node.lineno)
        elif not isinstance(node.ctx, ast.Load):
            raise NotImplementedError, (node, node.ctx, node.elts, node.lineno)

        self._s('new pyjslib.Tuple([')
        self._visit_list(node.elts)
        self._s("])")

    def visit_AugAssign(self, node):
        # AugAssign(expr target, operator op, expr value)
        self.visit(node.target)
        self.visit(node.op)
        self._s('=')
        self.visit(node.value)
        self._l(';')

    def visit_For(self, node):
        #                 var __i = xxx.__iter__();
        #         try {
        #             while (true) {
        #                 var i = __i.next();
        # pyjslib.printFunc([ i ], 1 );
        #             }
        #         } catch (e) {
        #             if (e != StopIteration) {
        #                 throw e;
        #             }
        #         }

        #('target', 'iter', 'body', 'orelse')
        if node.orelse:
            raise NotImplementedError, (node, node.lineno)
        # Attribute(expr value, identifier attr, expr_context ctx)
        # fields: ('targets', 'value')

        #Call(expr func, expr* args, keyword* keywords,
		#	 expr? starargs, expr? kwargs)

        iter_name = self._tmp_name(node)
        # assignement to tmp
        assign_iter = ast.Assign(
            (ast.Name(iter_name, ast.Store()),),
            ast.Call(
                ast.Attribute(node.iter, '__iter__', ast.Load()),
                [], [], [], []))
        self.visit(assign_iter)
        self._l('try {')
        self._l('while (true) {')

        assign_locals = ast.Assign(
            (node.target,),
            ast.Call(
                ast.Attribute(ast.Name(iter_name, ast.Load()), 'next',
                              ast.Load()),
                [], [], [], []))
        self.visit(assign_locals)
        for n in node.body:
            self.visit(n)
        self._l('}')
        self._l('} catch (__e) {')
        self._l('if (__e != StopIteration) {throw __e;};')

        # delete the iterator reference
        self.visit(ast.Delete((ast.Name(iter_name, ast.Load()),)))
        self._l('}')

    def visit_Delete(self, node):
        # Delete(expr* targets)
        for node in node.targets:
            self._s('delete')
            self.visit(node)
            self._l(';')


    # comparison operators
    def visit_Eq(self, node):
        self._s('===')
    def visit_NotEq(self, node):
        self._s('!==')
    def visit_Lt(self, node):
        self._s('<')
    def visit_LtE(self, node):
        self._s('<=')
    def visit_Gt(self, node):
        self._s('>')
    def visit_GtE(self, node):
        self._s('>=')

    visit_Is = _not_implemented
    visit_IsNot = _not_implemented
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

    visit_FloorDiv = _not_implemented
    visit_Pow = _not_implemented

    # not implemented expressions
    # visit_BinOp = _not_implemented not needed
    # visit_UnaryOp = _not_implemented not needed (not tested for all ops)
    visit_Lambda = _not_implemented
    visit_IfExp = _not_implemented
    visit_IfExp = _not_implemented
    visit_ListComp = _not_implemented
    visit_GeneratorExp = _not_implemented
    visit_Yield = _not_implemented
    visit_Repr = _not_implemented
    #-- the following expression can appear in assignment context


    # not implemented statements
    visit_With = _not_implemented
    visit_Raise = _not_implemented
    visit_TryExcept = _not_implemented
    visit_TryFinally = _not_implemented
    visit_Assert = _not_implemented
    visit_Exec = _not_implemented
    visit_Continue = _not_implemented
