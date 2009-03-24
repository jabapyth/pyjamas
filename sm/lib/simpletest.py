from other import A
class C:

    def x(self):
        pass


def in_global():
    def under_in_global():
        pass
    print 1


if __name__=='__main__':
    print "hoschi"

#import unittest
#from test.test_dict import DictTest

# class A:

#     x = 100

#     def __init__(self):
#         pass

# class B(A):

#     def __init__(self, x=10):
#         self.x = 2

# class C(B):

#     def __init__(self):
#         print "C", self.x
#         self.x = 10
        
# print A().x
# print B().x
# print C().x

#print '%s %s' % ('one', 'two')

# import other

# class B(other.A):
#     pass

# print B()

# class MyTest(DictTest):

#     def __init__(self):
#         x = 1

#     def runTest(self):
#         pass
#         #self.test_bool()
#         #self.test_keys()
#         #self.test_values()
#         #self.test_items()
#         #self.test_has_key()

# if __name__=='__main__':
#     print 1
#     #t = MyTest.__init__



# test.test_dict.test_main()t

# class A:

#     x = 10

#     @classmethod
#     def cm(cls, arg):
#         print cls
#         print arg

#     def im(self, arg):
#         print self
#         print arg


# class B:

#     x = 20

#     def bim(self):
#         print self.x

# a = A()
# b = B()
# #import pdb;pdb.set_trace()
# a.bim = b.bim

# print a.bim
# print b.bim

# def test():
#     print "test"
# a.test = test
# print type(A.cm), A.cm
# print type(A.im), dir(A.im)
# print type(a.cm), a.cm
# print type(a.im), a.im
# print type(a.test), a.test
# import pdb;pdb.set_trace()
# # print A.cm
# # print A.im
# # print a.cm
# # print a.im
# # A.cm(1)
# # a.cm(2)
# # a.im(3)
# # a.cm(4)
