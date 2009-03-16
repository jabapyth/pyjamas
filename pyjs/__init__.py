
import os

# pyjs.path is the list of paths, just like sys.path, from which
# library modules will be searched for, for compile purposes.
# obviously we don't want to use sys.path because that would result
# in compiling standard python modules into javascript!

path = [os.path.abspath('')]

if os.environ.has_key('PYJSPATH'):
    for p in os.environ['PYJSPATH'].split(os.pathsep):
        p = os.path.abspath(p)
        if os.path.isdir(p):
            path.append(p)




