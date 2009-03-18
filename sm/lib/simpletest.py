import pyjslib

class A:

    def getX(self):
        return 'a'

class B(A):

    def getX(self):
        return 'b'

def main():
    b = B()
    print b.getX()
    print A.getX()

if __name__=='__main__':
    main()
