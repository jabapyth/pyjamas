from pyjamas import Window
from pyjamas.ui import RootPanel
from pyjamas.ui.Button import Button

def greet(sender):
    Window.alert("Hello, AJAX!")

class Hello:
    def onModuleLoad(self):
        b = pyjamas.ui.Button("Click me", greet)
        pyjamas.ui.RootPanel().add(b)
