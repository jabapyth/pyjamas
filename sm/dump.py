#!/usr/bin/env python2.6
import ast
import sys
import os
from pprint import pprint

def main(path):
    f = open(path)
    tree = ast.parse(f.read())
    f.close()
    pprint(ast.dump(tree))

if __name__=='__main__':
    path = os.path.abspath(sys.argv[1])
    main(path)
