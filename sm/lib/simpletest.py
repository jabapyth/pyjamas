import pyjslib

class A:

    x = 1

    def setX(self, x):
        self.x = x

    def getX(self):
        return self.x

a = A()
print a.getX()

a.setX(5)
print a.getX()
