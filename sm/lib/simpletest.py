def outer_func(x):
    def inner_func(y):
        return y*2
    return inner_func(x)

print outer_func(2)
