from __pyjamas__  import JS
class HTTPRequest:
    def doCreateXmlHTTPRequest(self):
        JS("""
        return new ActiveXObject("Msxml2.XMLHTTP");
        """)

