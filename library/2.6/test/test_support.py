import unittest

verbose = True

class FakeStream(object):

    def __init__(self):
        self.s = ''

    def write(self, s):
        self.s = self.s + s

    def writeln(self, s):
        self.s = self.s + s + '\n'

    def flush(self):
        print self.s
        self.s = ''

class BasicTestRunner:

    def run(self, test):
        result = unittest.TestResult()
        test.run(result)
        return result

def run_unittest(*classes):
    """Run tests from unittest.TestCase-derived classes."""
    valid_types = (unittest.TestSuite, unittest.TestCase)
    suite = unittest.TestSuite()
    for cls in classes:
        if isinstance(cls, str):
            if cls in sys.modules:
                suite.addTest(unittest.findTestCases(sys.modules[cls]))
            else:
                raise ValueError("str arguments must be keys in sys.modules")
        elif isinstance(cls, valid_types):
            suite.addTest(cls)
        else:
            s = unittest.makeSuite(cls)
            suite.addTest(s)
    _run_suite(suite)

def _run_suite(suite):
    """Run tests from a unittest.TestSuite-derived class."""
    
    if verbose:
        runner = unittest.TextTestRunner(FakeStream(), verbosity=2)
    else:
        runner = BasicTestRunner()
    result = runner.run(suite)
    print "-----------done--------"
    if not result.wasSuccessful():
        if len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        elif len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        else:
            err = "errors occurred; run in verbose mode for details"
        raise TestFailed(err)

