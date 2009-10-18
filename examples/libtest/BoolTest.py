from UnitTest import UnitTest

class Stupid:
    pass

class Foo:

    def __init__(self, v):
        self._v = v

    def __nonzero__(self):
        return self._v>0

    def __len__(self):
        return 1

class Bar:

    def __init__(self, v):
        self._v = v

    def __len__(self):
        return self._v


class BoolTest(UnitTest):

    def testBaseTypes(self):
        # meta test first
        self.assertTrue(True)
        self.assertFalse(False)

        # booleans
        self.assertTrue(bool(True))
        self.assertFalse(bool(False))
        self.assertTrue(True == True)
        self.assertFalse(False == True)

        # ints
        self.assertTrue(bool(1))
        self.assertFalse(bool(0))
        self.assertTrue(1)
        self.assertFalse(0)

        # strings
        self.assertTrue(bool('a'))
        self.assertFalse(bool(''))
        self.assertTrue('a')
        self.assertFalse('')

    def testObjects(self):

        # objects
        self.assertTrue(bool(Stupid()))
        self.assertTrue(Stupid())

        # __nonzero__ has precedence
        self.assertFalse(bool(Foo(0)))
        self.assertTrue(bool(Foo(1)))
        self.assertFalse(Foo(0))
        self.assertTrue(Foo(1))

        # __len__ is used secondary
        self.assertFalse(bool(Bar(0)))
        self.assertTrue(bool(Bar(1)))
        self.assertFalse(Bar(0))
        self.assertTrue(Bar(1))


        # lists
        self.assertFalse(bool([]))
        self.assertTrue(bool([1]))
        self.assertFalse([])
        self.assertTrue([1])

        # dicts
        self.assertFalse(bool({}))
        self.assertTrue(bool({'x':1}))
        self.assertFalse({})
        self.assertTrue({'x':1})


    def testIfStatement(self):
        if([]):
            self.fail("Empty lists should not evaluate to True in If")
        else:
            self.assertTrue(True)
        if([1]):
            self.assertTrue(True)
	else:
            self.fail("None-empty lists should evaluate to True in If")
        if not []:
            self.assertTrue(True)
        else:
            self.fail("Non empty lists should not evaluate to True in If")
        if [1] and {}:
            self.fail("'[1] and {}' shoul evaluate to False")
        else:
            self.assertTrue(True)
        if [] or not {}:
            self.assertTrue(True)
        else:
            self.fail("'[] or not {}' shoul evaluate to True")
        if [] and not {}:
            self.fail("'[] and not {}' shoul evaluate to False")
        else:
            self.assertTrue(True)
        if 0 < 1 < 2:
            self.assertTrue(True)
        else:
            self.fail("if 0 < 1 < 2")
        i = [0, 2, 4]
        i = i.__iter__();
        if 0 < i.next() < 4:
            self.fail("iter (0)")
        else:
            self.assertTrue(True)
        if 0 < i.next() < 4:
            self.assertTrue(True)
        else:
            self.fail("iter (2)")
        if 0 < i.next() < 4:
            self.fail("iter (4)")
        else:
            self.assertTrue(True)


    def testWhileStatement(self):
        while([]):
            self.fail("Empty lists should not evaluate to True in While")
            break;
        while([1]):
            return
        self.fail("None-empty lists should evaluate to True in While")

    def testLogic(self):
    
        d = {'hello': 5}
        d2 = d or {}
        try:
            tst = d == d2
            self.assertTrue(tst, "#297 -non-empty object or {} should return the object")
        except TypeError:
            self.fail("#297 TypeError should not have been thrown")
            

        d = {}
        d2 = d or 5
        try:
            tst = d2 == 5
            self.assertTrue(tst, "#297 'empty object or 5' should return 5")
        except TypeError:
            self.fail("#297 TypeError should not have been thrown")

