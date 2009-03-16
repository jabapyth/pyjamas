module_global = "a string"

class AClass:

    class_attr = 1

    def getX(self):
        self.y = z = 2
        return self.class_attr

def test_func():
    global module_global
    module_func_local_attr = AClass()
    module_global = 1
    print  module_func_local_attr.getX()

# test_func(1, 2, 3)
# test_func(1, b=1)
# x = [1,2]
# test_func(*x)
# d = {'b':4}
# test_func(1, **d)

if __name__=='__main__':
    test_func()
