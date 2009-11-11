//*************************************************************************
// types
//*************************************************************************

$pyjs_TYPE_TYPE = "<type 'type'>";

$pyjs_TYPE_FUNCTION = "<type 'function'>";
$pyjs_TYPE_BUILTIN_FUNCTION_OR_METHOD = "<type 'builtin_function_or_method'>";
$pyjs_TYPE_INSTANCEMETHOD = "<type 'instancemethod'>";
$pyjs_TYPE_STATICMETHOD = "<type 'staticmethod'>";
$pyjs_TYPE_CLASSMETHOD = "<type 'classmethod'>";

$pyjs_TYPE_STR = "<type 'str'>"
$pyjs_TYPE_BOOL = "<type 'bool'>"
$pyjs_TYPE_FLOAT = "<type 'float'>"
$pyjs_TYPE_INT = "<type 'int'>"
$pyjs_TYPE_LONG = "<type 'long'>"

//*************************************************************************
// setup
//*************************************************************************

var $pyjs_array_slice = Array.prototype.slice;
var $pyjs_instances_id_counter = 0;

//*************************************************************************
//*************************************************************************
// arguments handling
//*************************************************************************

function $pyjs_kwargs_call(obj, func, star_args, dstar_args, args)
{
    if (obj !== null) {
        func = obj[func];
    }

    if ((func.__is_instance__ === true) && (typeof func['__call__'] != 'undefined')) {
      obj = func;
      func = func["__call__"];
    }

    // Merge dstar_args into args[0]
    if (dstar_args) {
        if (pyjslib.get_pyjs_classtype(dstar_args) != 'Dict') {
            throw (pyjslib.TypeError(func.__name__ + "() arguments after ** must be a dictionary " + pyjslib.repr(dstar_args)));
        }
        var i;
        /* use of __iter__ and next is horrendously expensive,
           use direct access to dictionary instead
         */
        for (var keys in dstar_args.__object) {
            var k = dstar_args.__object[keys][0];
            var v = dstar_args.__object[keys][1];

            if ($pyjs.options.arg_kwarg_multiple_values && typeof args[0][k] !=
 'undefined') {
                $pyjs__exception_func_multiple_values(func.__name__, k);
             }
            args[0][k] = v; 
        }

    }

    // Append star_args to args
    if (star_args) {
        if (star_args === null || typeof star_args.__iter__ != 'function') {
            throw (pyjslib.TypeError(func.__name__ + "() arguments after * must be a sequence" + pyjslib.repr(star_args)));
        }
        if (star_args.__array != null && star_args.__array.constructor == Array) {
            args = args.concat(star_args.__array);
        } else {

            /* use of __iter__ and next is horrendously expensive,
               use __len__ and __getitem__ instead, if they exist.
             */
            var call_args = Array();

            if (typeof star_args.__array != 'undefined') {
                var a = star_args.__array;
                var n = a.length;
                for (var i = 0; i < n; i++) {
                    call_args[i] = a[i];
                }
            } else {
                var $iter = star_args.__iter__();
                if (typeof $iter.__array != 'undefined') {
                    var a = $iter.__array;
                    var n = a.length;
                    for (var i = 0; i < n; i++) {
                        call_args[i] = a[i];
                    }
                } else if (typeof $iter.$genfun == 'function') {
                    var v, i = 0;
                    while (typeof (v = $iter.next(true)) != 'undefined') {
                        call_args[i++] = v;
                    }
                } else {
                    var i = 0;
                    try {
                        while (true) {
                            call_args[i++]=$iter.next();
                        }
                    } catch (e) {
                        if (e.__name__ != 'StopIteration') {
                            throw e;
                        }
                    }
                }
            }
            args = args.concat(call_args);
        }
    }

    // Now convert args to call_args
    // args = __kwargs, arg1, arg2, ...
    // _args = arg1, arg2, arg3, ... [*args, [**kwargs]]
    var _args = [];

    // Get function/method arguments
    if (typeof func.__args__ != 'undefined') {
        var __args__ = func.__args__;
    } else {
        var __args__ = new Array(null, null);
    }

    // Klass.method(instance, ...) call style
    if ((obj !== null) && (obj.__is_instance__ === false) && (func.__class__ == $pyjs_TYPE_INSTANCEMETHOD)) {
      __args__ = __args__.slice(); // duplicate
      self_name = func.im_func.__args__[2][0];
      __args__ = __args__.slice(0, 2).concat([[self_name]],
                                      __args__.slice(2));
    }

    var a, aname, _idx , idx, res;
    _idx = idx = 1;
    for (++_idx; _idx < __args__.length; _idx++, idx++) {
        aname = __args__[_idx][0];
        a = args[0][aname];
        if (typeof args[idx] == 'undefined') {
            _args.push(a);
            delete args[0][aname];
        } else {
            if (typeof a != 'undefined') $pyjs__exception_func_multiple_values(func.__name__, aname);
            _args.push(args[idx]);
        }
    }

    // Append the left-over args
    for (;idx < args.length;idx++) {
        if (typeof args[idx] != 'undefined') {
            _args.push(args[idx]);
        }
    }
    // Remove trailing undefineds
    while (_args.length > 0 && typeof _args[_args.length-1] == 'undefined') {
        _args.pop();
    }

    if (__args__[1] === null) {
        // Check for unexpected keyword
        for (var kwname in args[0]) {
            $pyjs__exception_func_unexpected_keyword(func.__name__, kwname);
        }
        return func.apply(obj, _args);
    }
    a = pyjslib.Dict(args[0]);
    a['$pyjs_is_kwarg'] = true;
    _args.push(a);
    res = func.apply(obj, _args);
    delete a['$pyjs_is_kwarg'];
    return res;
}

//*************************************************************************
//*************************************************************************
// exceptions
//*************************************************************************

function $pyjs__exception_func_param(func_name, minargs, maxargs, nargs) {
    if (minargs == maxargs) {
        switch (minargs) {
            case 0:
                var msg = func_name + "() takes no arguments (" + nargs + " given)";
                break;
            case 1:
                msg = func_name + "() takes exactly " + minargs + " argument (" + nargs + " given)";
                break;
            default:
                msg = func_name + "() takes exactly " + minargs + " arguments (" + nargs + " given)";
        };
    } else if (nargs > maxargs) {
        if (maxargs == 1) {
            msg  = func_name + "() takes at most " + maxargs + " argument (" + nargs + " given)";
        } else {
            msg = func_name + "() takes at most " + maxargs + " arguments (" + nargs + " given)";
        }
    } else if (nargs < minargs) {
        if (minargs == 1) {
            msg = func_name + "() takes at least " + minargs + " argument (" + nargs + " given)";
        } else {
            msg = func_name + "() takes at least " + minargs + " arguments (" + nargs + " given)";
        }
    } else {
        return;
    }
    if (typeof pyjslib.TypeError == 'function') {
        throw pyjslib.TypeError(String(msg));
    }
    throw msg;
}

function $pyjs__exception_func_multiple_values(func_name, key) {
    //throw func_name + "() got multiple values for keyword argument '" + key + "'";
    throw pyjslib.TypeError(String(func_name + "() got multiple values for keyword argument '" + key + "'"));
}

function $pyjs__exception_func_unexpected_keyword(func_name, key) {
    //throw func_name + "() got an unexpected keyword argument '" + key + "'";
    throw pyjslib.TypeError(String(func_name + "() got an unexpected keyword argument '" + key + "'"));
}

function $pyjs__exception_func_instance_expected(func_name, class_name, instance) {
        if (typeof instance == 'undefined') {
            instance = 'nothing';
        } else if (typeof instance.__is_instance__ == 'undefined') {
            instance = "'"+String(instance)+"'";
        } else {
            instance = String(instance);
        }
        //throw "unbound method "+func_name+"() must be called with "+class_name+" instance as first argument (got "+instance+" instead)";
        throw pyjslib.TypeError(String("unbound method "+func_name+"() must be called with "+class_name+" instance as first argument (got "+instance+" instead)"));
}

//*************************************************************************
//*************************************************************************
// classes handling
//*************************************************************************

function $pyjs__method(the_class, func) {
  // @return: method wrapper for the function
  method = function()
  {
    var self = this;
    var args;
    if (self.__is_instance__ === true) {
      args = [self];
      for (i = 0; i < arguments.length; i++) { args.push(arguments[i]); }
    } else {
      args = arguments;
      self = args[0];
    }

    if ($pyjs.options.arg_instance_type) {
      if (!pyjslib._isinstance(self, arguments.callee.im_class)) {
        $pyjs__exception_func_instance_expected(arguments.callee.__name__, 
                                  arguments.callee.im_class.toString(), self);
      }
    }

    return func.apply(self, args);
  };

  method.prototype = method;

  method.im_func = func;
  method.im_class = the_class;

  method.__name__ = func.__name__;
  method.__args__ = func.__args__.slice(0, 2).concat(func.__args__.slice(3)); // skip "self"
  method.__class__ = $pyjs_TYPE_INSTANCEMETHOD;
  return method;
}

function $pyjs__inherit_attr(juvenile, elder)
{
  for (var name in elder)
  {
    switch(name) {
      case "__id__":
      case "__name__":
      case "__module__":
      case "__class__":
      case "__dict__":
      case "__is_instance__":
      case "__super_classes__":
      case "__sub_classes__":
      case "__mro__":
      case "prototype":
        // don't inherit that
        break;
      default:
        juvenile[name] = elder[name];
    }
  }
}

function $pyjs__the_class(class_name, module)
{
    if (typeof module == "undefined") { module = null; }

    var the_class = function(){
        if (the_class.__number__ === null) {
            var instance = the_class['__new__'].apply(null, [the_class]);
        } else {
            var instance = the_class['__new__'].apply(null, [the_class, arguments]);
        }
        instance.__class__ = the_class;
        instance.__is_instance__ = true;
        instance.__dict__ = instance;
        instance.__id__ = String($pyjs_instances_id_counter++);

        if (instance['__init__'].apply(instance, arguments) != null) {
            throw pyjslib.TypeError('__init__() should return None');
        }

        return instance;
    };
    
    the_class.prototype = the_class;
    the_class.__name__ = class_name;
    the_class.__module__ = module;
    the_class.__class__ = $pyjs_TYPE_TYPE;
    the_class.__mro__ = new Array(the_class);

    the_class.__number__ = null;
    the_class.__dict__ = the_class;
    the_class.__is_instance__ = false;

    return the_class;
}

function $pyjs__mro_merge(seqs) {
    var res = new Array();
    var i = 0;
    var cand = null;
    function resolve_error(candidates) {
        throw (pyjslib.TypeError("Cannot create a consistent method resolution order (MRO) for bases " + candidates[0].__name__ + ", "+ candidates[1].__name__));
    }
    for (;;) {
        var nonemptyseqs = new Array();
        for (var j = 0; j < seqs.length; j++) {
            if (seqs[j].length > 0) nonemptyseqs.push(seqs[j]);
        }
        if (nonemptyseqs.length == 0) return res;
        i++;
        var candidates = new Array();
        for (var j = 0; j < nonemptyseqs.length; j++) {
            cand = nonemptyseqs[j][0];
            candidates.push(cand);
            var nothead = new Array();
            for (var k = 0; k < nonemptyseqs.length; k++) {
                for (var m = 1; m < nonemptyseqs[k].length; m++) {
                    if (cand == nonemptyseqs[k][m]) {
                        nothead.push(nonemptyseqs[k]);
                    }
                }
            }
            if (nothead.length != 0)
                cand = null; // reject candidate
            else
                break;
        }
        if (cand == null) {
            resolve_error(candidates);
        }
        res.push(cand);
        for (var j = 0; j < nonemptyseqs.length; j++) {
            if (nonemptyseqs[j][0] == cand) {
                nonemptyseqs[j].shift();
            }
        }
    }
    return res;
}

function $pyjs__class_merge_bases(the_class, cls_definition, bases)
{
    var base_mro_list = new Array();
    for (var i = 0; i < bases.length; i++) {
        __mro = bases[i].__mro__;
        if (typeof __mro == 'undefined') { __mro = [bases[i]]; }
        base_mro_list.push(new Array().concat(__mro));
    }
    var __mro__ = $pyjs__mro_merge(base_mro_list);

    for (var b = __mro__.length-1; b >= 0; b--) {
        var base = __mro__[b];
        $pyjs__inherit_attr(the_class, base);
    }
    $pyjs__inherit_attr(the_class, cls_definition);

    the_class.__id__ = cls_definition.__id__;

    the_class.__mro__ = new Array(the_class).concat(__mro__);

    the_class.__args__ = the_class["__init__"].__args__;
}

function $pyjs__class_supers_subs(the_class, bases)
{
    the_class.__super_classes__ = bases;
    the_class.__sub_classes__ = new Array();
    for (var i = 0; i < bases.length; i++) {
        if (typeof bases[i].__sub_classes__ == 'array') {
            bases[i].__sub_classes__.push(the_class);
        } else {
            bases[i].__sub_classes__ = new Array();
            bases[i].__sub_classes__.push(the_class);
        }
    }
}

/* creates a class, derived from bases, with methods and variables */
function $pyjs_type(clsname, bases, methods)
{
    var the_class = $pyjs__the_class(clsname);
    var cls_definition = new Object;
    for (var i in methods) {
      cls_definition[i] = methods[i];
    }
    $pyjs__class_merge_bases(the_class, cls_definition, bases);
    $pyjs__class_supers_subs(the_class, bases);
    return the_class;
}

