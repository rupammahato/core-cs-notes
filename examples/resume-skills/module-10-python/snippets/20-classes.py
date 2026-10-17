class Service:
    shared = []
    def __init__(self, name):
        self.name = name
    def label(self):
        return self.name
    @classmethod
    def create(cls, name):
        return cls(name)
    @staticmethod
    def valid(name):
        return bool(name)
a, b = Service.create('a'), Service('b')
a.shared.append('visible')
print(b.shared, a.label(), Service.valid(''))
print(a.label.__self__ is a)
