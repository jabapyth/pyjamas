module_global = "module_global"

# # TODO:classes without bases (incect object)
# class AClass:
#     pass

def test_func(x, y=2, z=3):
    print module_global
    print y

if __name__=='__main__':
    test_func(2, y=1)
