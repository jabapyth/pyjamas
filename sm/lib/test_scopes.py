import unittest
import other

z = 10

class ScopeTest(unittest.TestCase):

    x = 1

    def runTest(self):
        print "running test..."
        self.test_methods()
        self.test_other()
        self.test_error()
        self.test_isinstance()
        print "finished test"

    def test_isinstance(self):
        print "test_isinstance"
        a = other.A()
        self.failUnless(isinstance(a, other.A))

    def test_methods(self):
        print "test_methods"
        self.assertEqual(self.getX(), 1)
        self.x = 5
        self.assertEqual(self.getY(), 5)
        self.assertEqual(self.getZ(), 10)

    def test_other(self):
        print "test_other"
        a = other.A()


    def test_error(self):
        print "test_error"
        try:
            x = getattr(self, 'asdf')
        except AttributeError, e:
            return
        self.fail('AttributeError was not raised')


    @classmethod
    def getX(cls):
        return cls.x

    def getY(self):
        return self.x

    @staticmethod
    def getZ():
        return z

    def sort(self, compareFunc=None, keyFunc=None, reverse=False):
        if not compareFunc:
            compareFunc = cmp
        if keyFunc and reverse:
            def thisSort1(a,b):
                return -compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort1)
        elif keyFunc:
            def thisSort2(a,b):
                return compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort2)
        elif reverse:
            def thisSort3(a,b):
                return -compareFunc(a, b)
            self.l.sort(thisSort3)
        else:
            self.l.sort(compareFunc)

if __name__=='__main__':
    t = ScopeTest()
    t.runTest()


