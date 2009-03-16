# XXX hack for importing pyjslib, schould be differen like __builtins__
import pyjslib
import unittest
#import unittest
#from pyjamas import DOM
#from pyjamas.ui import Label

class MyTest(unittest.TestCase):
    def runTests(self):
        print 1
#     def test_1(self):
#         print 1

def main():
    #suite = unittest.TestSuite()
    tc = MyTest()
    tc.run()
    #unittest.run_unittest(MyTest)

if __name__=='__main__':
    main()
