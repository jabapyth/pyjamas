module_global = "a string"

class AClass:

    class_attr = 1

    def getX(self, x=3, y=4):
        print x
        print y

def test_func(a, b=1, c=2):
    print a
    print b
    print c


test_func(1, 2, 3)
test_func(1, b=1)
x = [1,2]
test_func(*x)
d = {'b':4}
test_func(1, **d)

if __name__=='__main__':
    test_func(1)
