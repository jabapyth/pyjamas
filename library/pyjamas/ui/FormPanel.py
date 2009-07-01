# Copyright 2006 James Tauber and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pyjamas import DOM

from pyjamas.ui.SimplePanel import SimplePanel
from pyjamas.ui import Event
from pyjamas.ui.EventObject import EventObject

class FormSubmitEvent(EventObject):
    def __init__(self, source):
       EventObject.__init__(self, source)
       self.cancel = False # ?

    def isCancelled(self):
       return self.cancel

    def setCancelled(self, cancel):
       self.cancel = cancel

class FormSubmitCompleteEvent(EventObject):
    def __init__(self, source, results):
       EventObject.__init__(self, source)
       self.results = results
    def getResults(self):
       return self.results

FormPanel_formId = 0

class FormPanel(SimplePanel):
    ENCODING_MULTIPART = "multipart/form-data"
    ENCODING_URLENCODED = "application/x-www-form-urlencoded"
    METHOD_GET = "get"
    METHOD_POST = "post"

    def __init__(self, target = None):
        global FormPanel_formId

        if hasattr(target, "getName"):
            target = target.getName()

        SimplePanel.__init__(self, DOM.createForm())

        self.formHandlers = []
        self.iframe = None

        FormPanel_formId += 1
        formName = "FormPanel_" + str(FormPanel_formId)
        DOM.setAttribute(self.getElement(), "target", formName)
        DOM.setInnerHTML(self.getElement(), "<iframe name='" + formName + "'>")
        self.iframe = DOM.getFirstChild(self.getElement())

        DOM.setIntStyleAttribute(self.iframe, "width", 0)
        DOM.setIntStyleAttribute(self.iframe, "height", 0)
        DOM.setIntStyleAttribute(self.iframe, "border", 0)

        self.sinkEvents(Event.ONLOAD)

        if target != None:
            self.setTarget(target)

    def addFormHandler(self, handler):
        self.formHandlers.append(handler)

    def getAction(self):
        return DOM.getAttribute(self.getElement(), "action")

    # FormPanelImpl.getEncoding
    def getEncoding(self):
        return self.getElement().enctype

    def getMethod(self):
        return DOM.getAttribute(self.getElement(), "method")

    def getTarget(self):
        return DOM.getAttribute(self.getElement(), "target")

    # FormPanelImpl.getTextContents
    def getTextContents(self, iframe):
        try:
            if not iframe.contentDocument:
                return None
            return DOM.getInnerHTML(iframe.contentDocument.body)
        except:
            return None

    # FormPanelImpl.hookEvents
    def hookEvents(self, iframe, form, listener):
        # TODO: might have to fix this, use DOM.set_listener()
        self._listener = listener
        if iframe:
            iframe.connect("browser-event", self._onload)
            iframe.addEventListener("load", True)

        form.connect("browser-event", self._onsubmit)
        form.addEventListener("onsubmit", True)

    def onFormSubmit(self):
        event = FormSubmitEvent(self)
        for handler in self.formHandlers:
            handler.onSubmit(event)

        return not event.isCancelled()

    def onFrameLoad(self):
        event = FormSubmitCompleteEvent(self, self.getTextContents(self.iframe))
        for handler in self.formHandlers:
            handler.onSubmitComplete(event)

    def removeFormHandler(self, handler):
        self.formHandlers.remove(handler)

    def setAction(self, url):
        DOM.setAttribute(self.getElement(), "action", url)

    # FormPanelImpl.setEncoding
    def setEncoding(self, encodingType):
        form = self.getElement()
        form.enctype = encodingType
        form.encoding = encodingType

    def setMethod(self, method):
        DOM.setAttribute(self.getElement(), "method", method)

    def submit(self):
        event = FormSubmitEvent(self)
        for handler in self.formHandlers:
            handler.onSubmit(event)

        if event.isCancelled():
            return

        self.submitImpl(self.getElement(), self.iframe)

    # FormPanelImpl.submit
    def submitImpl(self, form, iframe):
        if iframe:
            iframe._formAction = form.action
        form.submit()

    def onAttach(self):
        SimplePanel.onAttach(self)
        self.hookEvents(self.iframe, self.getElement(), self)

    def onDetach(self):
        SimplePanel.onDetach(self)
        self.unhookEvents(self.iframe, self.getElement())

    def setTarget(self, target):
        DOM.setAttribute(self.getElement(), "target", target)

    # FormPanelImpl.unhookEvents
    def unhookEvents(self, iframe, form):
        print "TODO: unhookEvents"

