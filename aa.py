from vanstein.decorators import async_func
from vanstein.loop import BaseAsyncLoop

loop = BaseAsyncLoop()


@async_func
def a():
    print("Hello, world!")


loop.run(a())
