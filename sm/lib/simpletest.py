module_global = "module_global"

# # TODO:classes without bases (incect object)
class AClass:

    def getX(self, y, z):
        return self.x

def test_func(x=1, y=2):
    a = AClass()
    a.getX(1,2)


if __name__=='__main__':
    test_func(1)
