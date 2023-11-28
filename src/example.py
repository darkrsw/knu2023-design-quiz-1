class First():
    def __init__(self):
        print "first"

class Second(First):
    def __init__(self):
        print "second"
        
class Third(Second):
    def __init__(self):
        print "that's it"
        
class A():
    def __init__(self):
        pass
        
class B(A):
    def __init__(self):
        pass

class C():
    def __init__(self):
        pass

class D(A):
    def __init__(self):
        pass
