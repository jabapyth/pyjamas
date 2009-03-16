def JS(s):
    """fake js to make python compiler happy"""
    pass

class Console:

    def error(self, *args):
        pass
    debug = log = error

console = Console()
