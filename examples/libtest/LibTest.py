import sys

from StringTest import StringTest
from ListTest import ListTest
from ClassTest import ClassTest
from SetTest import SetTest
from ArgsTest import ArgsTest
from VarsTest import VarsTest
from AttributeTest import AttributeTest
from ExceptionTest import ExceptionTest
from BoolTest import BoolTest
from FunctionTest import FunctionTest
from NameTest import NameTest
from DictTest import DictTest
# TODO: add import into pyjs.py _stmt
#if sys.platform in ['mozilla', 'ie6', 'opera', 'oldmoz', 'safari']:
#    from JSOTest import JSOTest
from BuiltinTest import BuiltinTest
from MD5Test import MD5Test

def main():

    BoolTest().run()
    ListTest().run()
    FunctionTest().run()
    ExceptionTest().run()
    ClassTest().run()
    StringTest().run()
    SetTest().run()
    ArgsTest().run()
    VarsTest().run()
    AttributeTest().run()
    NameTest().run()
    DictTest().run()
#    if sys.platform in ['mozilla', 'ie6', 'opera', 'oldmoz', 'safari']:
#        JSOTest().run()
    BuiltinTest().run()
    MD5Test().run()

if __name__ == '__main__':
    main()


