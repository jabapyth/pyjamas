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
from __pyjamas__ import JS, console
from pyjamas import DOM
from pyjamas import pygwt
from DeferredCommand import DeferredCommand
import pyjslib
from History import History
from pyjamas import Window
from sets import Set


from pyjamas.ui import TreeItem

class RootTreeItem(TreeItem):
    def addItem(self, item):
        if (item.getParentItem() != None) or (item.getTree() != None):
            item.remove()
        item.setTree(self.getTree())

        item.setParentItem(None)
        self.children.append(item)

        DOM.setIntStyleAttribute(item.getElement(), "marginLeft", 0)

    def removeItem(self, item):
        if item not in self.children:
            return

        item.setTree(None)
        item.setParentItem(None)
        self.children.remove(item)


