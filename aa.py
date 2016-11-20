from vanstein.decorators import async_func
from vanstein.loop import BaseAsyncLoop

loop = BaseAsyncLoop()


def b():
    print("b")
    raise RuntimeError


@async_func
def a():
    print("Hello, world!")
    try:
        x = b()
    except:
        print("caught")
        x = 2
    return x


i = loop.run(a())
print(i)
