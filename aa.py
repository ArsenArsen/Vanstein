import sys

sys.stderr = sys.stdout

from vanstein.decorators import async_func
from vanstein.loop import BaseAsyncLoop

loop = BaseAsyncLoop()


class XD(object):
    def __init__(self):
        self.x = 1


def b():
    print("inside b")
    return XD()


@async_func
def a():
    return b()


i = loop.run(a())
print(i.x)
