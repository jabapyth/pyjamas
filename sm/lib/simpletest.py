import pyjslib

class A:

    x = 1

    l = [1,2,3]

    def setX(self, x):
        self.x = x

    def getX(self):
        return self.x

a = A()
#print a.getX()

#a.setX(5)
#print a.getX()

a.l.append(100)
A.l.append(1000)
for i in a.l:
    print i

# i = 1
# while True:
#     i += 1
#     print i
#     if i>3:
#         break
