class Path():
    def __init__(self):
        print("first")

class Walk(Path):
    def __init__(self):
        print("second")


class Cycle(Walk):
    def __init__(self):
        print("that's it")


class Bipartite():
    def __init__(self):
        pass


class Connectivity(Bipartite):
    def __init__(self):
        pass


class Planar():
    def __init__(self):
        pass


class GraphColor(Bipartite):
    def __init__(self):
        pass

