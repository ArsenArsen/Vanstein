"""
Vanstein exception system.

This hijacks default exceptions to make them work with CPython code.
"""

from forbiddenfruit import curse

from vanstein.context import _VSContext
from vanstein.decorators import native_invoke


class _VSTraceback(object):
    """
    Represents a mock traceback.
    """

    def __init__(self, root: _VSContext):
        self._root = root

    @property
    def tb_frame(self) -> '_VSContext':
        # Context objects act as frame objects too.
        return self._root

    @property
    def tb_lasti(self):
        return self._root.f_lasti

    @property
    def tb_lineno(self):
        return self._root.f_lineno

    @property
    def tb_next(self):
        if self._root.next_ctx is None:
            return None
        return type(self)(self._root.next_ctx)


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
        try:
            return super(BaseException, self).__traceback__
        except AttributeError:
            return None


curse(BaseException, "__traceback__", property(get_traceback))


@native_invoke
def create_traceback(ctx: _VSContext) -> _VSTraceback:
    """
    Creates a traceback object from a context.

    This will iterate down the `prev_ctx` of each context to find the root context.
    :param ctx: The context to use.
    """
    curr_ctx = ctx
    while True:
        if curr_ctx.prev_ctx is None:
            break
        else:
            curr_ctx = curr_ctx.prev_ctx

    return _VSTraceback(curr_ctx)


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
    # Create a traceback for this exception.
    exception._tb = create_traceback(ctx)
    # Inject the exception.
    ctx.inject_exception(exception)
    return ctx


@native_invoke
def get_ordered_call_stack(start_ctx: _VSContext):
    """
    Gets the ordered call stack from the start context.
    """
    frames = []
    while start_ctx.next_ctx is not None:
        frames.append(start_ctx)
        start_ctx = start_ctx.prev_ctx

    # Reverse the frames, as they've been added in reverse order.
    return frames
