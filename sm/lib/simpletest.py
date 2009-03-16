module_global = "module_global"

# # TODO:classes without bases (incect object)
# class AClass:
#     pass

def test_func(x, y=2, z=3):
    print x
    print y
    print z
    print module_global


if __name__=='__main__':
    test_func("x", z="z", y="y")
    test_func("x", y="y")
    test_func(1)
