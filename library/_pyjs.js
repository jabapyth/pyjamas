var pyjs_instancemethod = function (im_func, im_self, im_class) {
  return function(){
    var args = arguments;
    if (this instanceof im_class){
      args = [this];
      for (var i=0; i<arguments.length; i++){
        args.push(arguments[i]);
      }
    };
    return im_func.apply(null, args);
  };
};

function pyjs_type(name, base, spec, parent){
  var klass = spec || function(){};
  pyjs_extend(klass, base);
  klass.prototype.__class__.__name__ =  name;
  klass.prototype.__class__.__new__ = function (){
    var instance = new klass();
    var args = [instance];
    // why not concat??? js sucks
    for (var i=0; i<arguments.length; i++){
      args.push(arguments[i]);
    }
    if (instance.__init__) {instance.__init__.apply(null, args)};
    return instance;
  };
  klass.prototype.__class__.__new__.__name__ = name;
  klass.prototype.__class__.__name__ = name;
  klass.prototype.__class__.__new__.__constructors = [klass].concat(
    base.__constructors__);
  if(parent){
    parent[name] = klass.prototype.__class__.__new__;
    klass.prototype.__class__.__module__ = parent.__name__;
  }
  return klass;
};

function pyjs_extend(klass, base) {
    function klass_object_inherit() {}
    klass_object_inherit.prototype = base.prototype;
    klass_object = new klass_object_inherit();
    for (var i in base.prototype.__class__) {
        v = base.prototype.__class__[i];
        if (typeof v == "function" && (v.class_method || v.static_method || v.unbound_method))
        {
            klass_object[i] = v;
        }
    }

    function klass_inherit() {}
    klass_inherit.prototype = klass_object;
    klass.prototype = new klass_inherit();
    klass_object.constructor = klass;
    klass.prototype.__class__ = klass_object;

    for (var i in base.prototype) {
        v = base.prototype[i];
        if (typeof v == "function" && v.instance_method)
        {
            klass.prototype[i] = v;
        }
    }
}

function pyjs_kwargs_function_call(func, args)
{
    return func.apply(null, func.parse_kwargs.apply(null, args));
}

function pyjs_kwargs_method_call(obj, method_name, args)
{
    var method = obj[method_name];
    return method.apply(obj, method.parse_kwargs.apply(null, args));
}

// String.prototype.__getitem__ = String.prototype.charAt;
// String.prototype.upper = String.prototype.toUpperCase;
// String.prototype.lower = String.prototype.toLowerCase;
// String.prototype.find=pyjslib.String_find;
// String.prototype.join=pyjslib.String_join;
// String.prototype.isdigit=pyjslib.String_isdigit;
// String.prototype.__iter__=pyjslib.String___iter__;

// String.prototype.__replace=String.prototype.replace;
// String.prototype.replace=pyjslib.String_replace;

// String.prototype.split=pyjslib.String_split;
// String.prototype.strip=pyjslib.String_strip;
// String.prototype.lstrip=pyjslib.String_lstrip;
// String.prototype.rstrip=pyjslib.String_rstrip;
// String.prototype.startswith=pyjslib.String_startswith;

// var str = String;

