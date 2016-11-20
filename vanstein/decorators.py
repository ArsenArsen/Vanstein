"""
Common decorators.
"""
from vanstein.context import VSWrappedFunction


def native_invoke(func):
    """
    Marks a function for **native invokation**.

    This means that calling this function will not step out at any point - the CPython bytecode engine runs the
    function instead of the Vanstein bytecode engine.

    This has several issues you must be aware of:

        - You cannot pause the function once it has started.

    The only exception (no pun intended) to that last rule are built-in functions, which will attempt to handle
    exceptions properly inside the VS bytecode context.

    :param func: The function to decorate.
    :return: A modified function object.
    """
    # lol this is all we do
    func._native_invoke = True
    return func


def async_func(func):
    """
    Marks a function for **Vanstein execution.**

    This signifies to the event loop to run this function inside VS, and not inside CPython.

    Example usage:
    .. code:: python

        loop = vanstein.get_event_loop()
        loop.run(some_func(1, 2, 3))

    :param func: The func to decorate.
    :return: A new :class:`vanstein.context.VSWrappedFunction`.
    """
    return VSWrappedFunction(func)
