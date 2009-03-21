import pyjslib
# import unittest
# from test.test_dict import DictTest

# class T(DictTest):
#     def runTest(self):
#         print 1

# t = T()
# t.test_bool()

class MyTest:

    def __init__(self, x):
        self.x = x
    
    def test_1(self):
        self.failUnless(0)
    test_2 = test_1


if __name__=='__main__':
    t = MyTest()
    t.test_1()


# test.test_dict.test_main()t

# class A:

#     exc = AttributeError

#     def xxx(self):
#         print 1
#     yyy = xxx

# a = A()

# a.yyy()

# class B:

#     x = 1

#     def __init__(self, x):
#         self.x = x

#     def toString(self):
#         return "instance of b " + self.x

# class A:

#     a_count = 0
#     b_in_a = B

#     def __init__(self, ipar):
#         self.instance_attr = ipar

#     def imethod(self):
#         self.instance_attr

#     def createB(self, i):
#         return self.b_in_a(i)

# a = A(1)
# b = B(2)
# print a.b_in_a(3)
# print a.createB(4)
