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
from __pyjamas__ import JS
from pyjamas import DOM

class Focus:

    def blur(self, elem):
        JS("""
        elem.blur();
        """)

    def createFocusable(self):
        JS("""
        var e = $doc.createElement("DIV");
        e.tabIndex = 0;
        return e;
        """)

    def focus(self, elem):
        JS("""
        elem.focus();
        """)

    def getTabIndex(self, elem):
        JS("""
        return elem.tabIndex;
        """)

    def setAccessKey(self, elem, key):
        JS("""
        elem.accessKey = key;
        """)

    def setTabIndex(self, elem, index):
        JS("""
        elem.tabIndex = index;
        """)


