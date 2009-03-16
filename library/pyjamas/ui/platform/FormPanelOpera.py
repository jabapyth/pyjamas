from __pyjamas__  import JS
from __pyjamas__  import JS
from __pyjamas__  import JS
# FocusImplOld
class FormPanel:
    def getTextContents(self, iframe):
        JS("""
        try {
            if (!iframe.contentWindow.document)
                return null;
    
            return iframe.contentWindow.document.body.innerText;
        } catch (e) {
            return null;
        }
        """)
