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

class PopupPanel(SimplePanel):
    def __init__(self, autoHide=False, modal=True):
        self.popupListeners = []
        self.showing = False
        self.autoHide = False
        self.modal = modal

        SimplePanel.__init__(self, self.createElement())
        DOM.setStyleAttribute(self.getElement(), "position", "absolute")
        if autoHide:
            self.autoHide = autoHide

    def addPopupListener(self, listener):
        self.popupListeners.append(listener)

    def getPopupLeft(self):
        return DOM.getIntAttribute(self.getElement(), "offsetLeft")

    def getPopupTop(self):
        return DOM.getIntAttribute(self.getElement(), "offsetTop")

    # PopupImpl.createElement
    def createElement(self):
        return DOM.createDiv()

    def hide(self, autoClosed=False):
        if not self.showing:
            return
        self.showing = False
        DOM.removeEventPreview(self)

        RootPanel().get().remove(self)
        self.onHideImpl(self.getElement())
        for listener in self.popupListeners:
            if listener.onPopupClosed: listener.onPopupClosed(self, autoClosed)
            else: listener(self, autoClosed)

    def isModal(self):
        return self.modal

    def onEventPreview(self, event):
        target = DOM.eventGetTarget(event)
        event_targets_popup = target and DOM.isOrHasChild(self.getElement(), target)
        type = DOM.eventGetType(event)
        #print "onEventPreview popup", type, event_targets_popup
        if type == "keydown":
            return (    self.onKeyDownPreview(
                            DOM.eventGetKeyCode(event),
                            KeyboardListener.getKeyboardModifiers(self, event)
                            )
                    and (event_targets_popup or not self.modal)
                   )
        elif type == "keyup":
            return (    self.onKeyUpPreview(
                            DOM.eventGetKeyCode(event),
                            KeyboardListener.getKeyboardModifiers(self, event)
                            )
                    and (event_targets_popup or not self.modal)
                   )
        elif type == "keypress":
            return (    self.onKeyPressPreview(
                            DOM.eventGetKeyCode(event),
                            KeyboardListener.getKeyboardModifiers(self, event)
                            )
                    and (event_targets_popup or not self.modal)
                   )
        elif type == "mousedown":
            if DOM.getCaptureElement() != None:
                return True
            if not event_targets_popup and self.autoHide:
                self.hide(True)
                return True
        elif (   type == "mouseup"
              or type == "mousemove"
              or type == "click"
              or type == "dblclick"
             ):
            if DOM.getCaptureElement() != None:
                return True
        return not self.modal or event_targets_popup

    def onKeyDownPreview(self, key, modifiers):
        return True

    def onKeyPressPreview(self, key, modifiers):
        return True

    def onKeyUpPreview(self, key, modifiers):
        return True

    # PopupImpl.onHide
    def onHideImpl(self, popup):
        pass

    # PopupImpl.onShow
    def onShowImpl(self, popup):
        pass

    def removePopupListener(self, listener):
        self.popupListeners.remove(listener)

    def setPopupPosition(self, left, top):
        if left < 0:
            left = 0
        if top < 0:
            top = 0

        element = self.getElement()
        DOM.setStyleAttribute(element, "left", left + "px")
        DOM.setStyleAttribute(element, "top", top + "px")

    def show(self):
        if self.showing:
            return

        self.showing = True
        DOM.addEventPreview(self)

        RootPanel().get().add(self)
        self.onShowImpl(self.getElement())


