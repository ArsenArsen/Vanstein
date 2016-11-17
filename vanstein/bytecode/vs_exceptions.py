"""
Vanstein exception system.

This hijacks default exceptions to make them work with CPython code.
"""

from forbiddenfruit import curse

from vanstein.context import _VSContext
from vanstein.decorators import native_invoke


def get_traceback(self):
    """
    Hijacked item for `__traceback__`.

    This will overwrite `__traceback__` on the Exception class.
    """
    try:
        # Return our hijacked traceback.
        return self._tb
    except AttributeError:
        # Explicit super() call otherwise CPython freaks out.
        return super(BaseException, self).__traceback__


curse(BaseException, "__traceback__", property(get_traceback))


# Now we've done that, define the `safe_raise` function.

@native_invoke
def safe_raise(ctx: _VSContext, exception: BaseException):
    """
    Attempts to "safely" raise an exception into the context.

    If the exception is being handled by a `try` block, it will automatically move the pointer to the Except block
    that is consistent with it.

    Otherwise, it will attempt to bubble it out of the stack.
    :param ctx: The context to raise into.
    :param exception: The exception to raise.
    :return: The context.
    """
    # todo: set tracebacks
    # inject the exception
    ctx.inject_exception(exception)
    # this will set the state to EXCEPTION, which the event loop will catch and bubble up.
    return ctx


@native_invoke
def get_ordered_call_stack(end_ctx: _VSContext):
    """
    Gets the ordered call stack from an end context.
    """
    frames = []
    while end_ctx.prev_ctx is not None:
        frames.append(end_ctx)
        end_ctx = end_ctx.prev_ctx

    # Reverse the frames, as they've been added in reverse order.
    return frames[::-1]
