from pyjamas.ui import Composite

class Sink(Composite):
    def __init__(self, name):
        Composite.__init__(self)
        self.name = name
    
    def onHide(self):
        pass
        
    def onShow(self):
        pass

    def baseURL(self):
        return ""

class SinkInfo:
    def __init__(self, name, desc, object_type):
        self.name=name
        self.description=desc
        self.object_type=object_type
        self.instance=None

    def createInstance(self):
        if hasattr(self.object_type, "__new__"):
            obj = self.object_type.__new__()
        else:
            obj = self.object_type()
        obj.name = self.name
        return obj

    def getDescription(self):
        return self.description

    def getInstance(self):
        if self.instance==None:
            self.instance=self.createInstance()
        return self.instance
    
    def getName(self):
        return self.name
    
