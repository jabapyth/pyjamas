import pyjslib

xxx = {}

def main():
    try:
        x = xxx['asdf']
    except KeyError:
        print "not found"


if __name__ == '__main__':
    main()
