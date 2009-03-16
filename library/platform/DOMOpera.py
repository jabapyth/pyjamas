from __pyjamas__  import JS
def eventGetButton(evt):
    JS("""
    var button = evt.button;
    if(button == 0){
        return 1;
    } else {
        return button;
    }
    """)
