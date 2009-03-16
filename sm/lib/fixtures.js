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
    console = {};
    console.debug = print;
