from __pyjamas__  import JS
from __pyjamas__  import JS
from __pyjamas__  import JS
# FocusImplOld
class FormPanel:
    def getEncoding(self, form):
        JS("""
        return form.enctype;
        """)

    def setEncoding(self, form, encoding):
        JS("""
        form.enctype = encoding;
        """)

