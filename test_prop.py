class Foo:
    @property
    def myprop(self):
        return "val"

f = Foo()
print(f.myprop)
