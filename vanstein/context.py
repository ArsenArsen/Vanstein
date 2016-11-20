"""
Contexts contain the state of a suspended coroutine.
"""
import dis
# This uses Enum34 for Python 3.3 and below.
import enum

# Sentinel value which means no result.
import collections
import types

NO_RESULT = type("NO_RESULT", (), {})


class VSCtxState(enum.Enum):
    # Waiting to be run.
    # This can mean it's returned from another function.
    PENDING = 0

    # Currently running.
    # The Context from `loop.current_ctx` should have this.
    RUNNING = 1

    # Waiting for another coroutine to finish running.
    SUSPENDED = 3

    # The result is done.
    FINISHED = 4

    # The context has errored.
    ERRORED = 5


class _VSContext(object):
    """
    The raw context class for a function.

    This should NOT be created directly.
    """

    def __init__(self, function):
        # This shouldn't be called.
        self._actual_function = function

        # Initial state is PENDING.
        # We change this when we switch contexts.
        self.state = VSCtxState.PENDING

        # The done callback.
        # This is automatically called when our state switches to FINISHED i.e when we've executed fully.
        # This usually just notifies our dependant task that we have a result.
        self._done_callback = None

        # The result of our underlying function.
        # This is only not NO_RESULT when the state is FINISHED.
        self._result = NO_RESULT

        # Vanstein bytecode internals.

        # The current list of instructions.
        self._instructions = []

        # The current stack for this function.
        # This is used when executing bytecode that edits the stack.
        self.stack = collections.deque(maxlen=self.__code__.co_stacksize)

        # The current names and varnames.
        # These are only the actual values, NOT the names.
        # Use the co_names property for that.
        self.names = [NO_RESULT for i in self.co_names]
        self.varnames = [NO_RESULT for i in self.co_varnames]

        # The current instruction pointer.
        # This represents what instruction in the list of instructions is currently being ran.
        self.instruction_pointer = -1

        # The previous context in the frame.
        # This is used for bubbling exceptions out.
        # If this is None, it means it has no previous context.
        self.prev_ctx = None

        # The next context in the frame.
        # This makes the contexts a doubly linked list.
        self.next_ctx = None

        # Exception handling.
        self._handling_exception = False
        self._exception_state = None

        self._exception_callback = None

        # The next exception pointer.
        # What does this do? It points to where we should go if an exception was raised.
        self.exc_next_pointer = 0

    def _safe_raise(self, exception: TypeError):
        """
        Safely raises an exception.

        If this is inside the event loop, it will set this exception to errored.
        Otherwise, it will raise it normally.
        """
        if self.next_ctx is None or self.prev_ctx is None:
            self.inject_exception(exception)
        else:
            raise exception

    def fill_args(self, *args):
        """
        Fill in arguments.

        This sets VARNAMES up to len(args) with these values.
        """
        for n, item in enumerate(args):
            try:
                self.varnames[n] = item
            except IndexError:
                self._safe_raise(TypeError("{}() takes {} positional arguments but {} were given".format(
                    self._actual_function.__name__, self.__code__.co_argcount, len(args)
                )))

        return self

    @property
    def tos(self):
        """
        TOS -> Top of Stack
        """
        return self.stack[-1]

    def push(self, item: object):
        """Push onto the stack."""
        self.stack.append(item)

    def pop(self):
        """Pop off of the stack."""
        return self.stack.pop()

    @property
    def result(self):
        if self.state is not VSCtxState.FINISHED:
            raise RuntimeError("Context is not finished.")
        return self._result

    @property
    def instructions(self):
        if not self._instructions:
            self._instructions = list(dis.get_instructions(self))

        return self._instructions

    @property
    def current_instruction(self):
        return self.instructions[self.instruction_pointer]

    def next_instruction(self):
        """
        :return: The next instruction to be run.
            This moves the pointer up by one.
        """
        self.instruction_pointer += 1
        return self.current_instruction

    def __repr__(self):
        return "<_VSContext state={} function={} pointer={} stack={}>".format(self.state,
                                                                              self._actual_function,
                                                                              self.instruction_pointer,
                                                                              self.stack)

    # Bytecode properties.

    @property
    def __code__(self) -> types.CodeType:
        """
        :return: The code object for this function. 
        """
        return self._actual_function.__code__

    @property
    def co_names(self) -> tuple:
        return self.__code__.co_names

    @property
    def co_consts(self) -> tuple:
        return self.__code__.co_consts

    @property
    def co_varnames(self) -> tuple:
        return self.__code__.co_varnames

    @property
    def co_argcount(self):
        return self.__code__.co_argcount

    # Frame properties.
    @property
    def f_back(self) -> '_VSContext':
        return self.prev_ctx
    
    @property
    def f_builtins(self):
        return __builtins__
    
    @property
    def f_globals(self):
        return self.__globals__
    
    @property
    def f_lasti(self):
        return self.instructions[self.instruction_pointer].offset

    def _get_current_line_number(self):
        starts_line = self.instructions[self.instruction_pointer].starts_line
        local_pointer = self.instruction_pointer - 1

        while not starts_line:
            if local_pointer < 0:
                return None

            starts_line = self.instructions[local_pointer].starts_line
            local_pointer -= 1

        return starts_line

    @property
    def f_lineno(self):
        i = self._get_current_line_number()
        return i

    f_code = __code__
    
    @property
    def f_trace(self):
        return None
    
    @property
    def f_restricted(self):
        return 0

    @property
    def __globals__(self):
        return self._actual_function.__globals__

    def get_global(self, name: str):
        """
        Gets a global from the global list.
        """
        try:
            return self.__globals__[name]
        except KeyError:
            return __builtins__[name]

    def add_done_callback(self, callback: callable):
        if self.state is VSCtxState.FINISHED:
            raise RuntimeError("Cannot add callback to finished context")

        self._done_callback = callback

    def add_exception_callback(self, callback: callable):
        if self.state is VSCtxState.FINISHED:
            raise RuntimeError("Cannot add callback to finished context")

        self._exception_callback = callback

    def finish(self):
        try:
            self._done_callback(self._result)
        except TypeError:
            return

    def _on_result_cb(self, result: None):
        # Default done callback.
        # This is called when a context is willing to notify its upstream context.
        # Push the result onto TOS.
        self.push(result)

        # Remove our next_ctx.
        self.next_ctx = None

        # Switch our state to PENDING.
        # This means we're ready to run on the event loop again.
        self.state = VSCtxState.PENDING

    def _on_exception_cb(self, exception: BaseException):
        # Put the traceback on the stack -> TOS2.
        self.push(exception.__traceback__)
        # Put the __from__ on the stack -> TOS1.
        self.push(exception.__cause__)
        # Put the exception on the stack -> TOS.
        self.push(exception)

        # Set our exception state.
        self._exception_state = exception
        self._handling_exception = True

        # Set the current pointer to the current exception pointer.
        if self.exc_next_pointer:
            self.instruction_pointer = self.exc_next_pointer
            # Switch ourselves to PENDING, so that the event loop knows we're ready to run again.
            self.state = VSCtxState.PENDING
        else:
            # There's no exc_next_pointer.
            # This means we can't jump to anywhere; instead we set our state to ERRORED.
            self.state = VSCtxState.ERRORED

    def inject_exception(self, exception: BaseException):
        """
        Injects an exception into the current context.

        This does nothing YET. However, it will set `_handling_exception` to True, which will signal the VM that the
        context is currently in an exception context, and should re-raise when a FINALLY is reached.

        :param exception: The exception to inject.
        """
        # Set the current exception state.
        self._exception_state = exception
        self._handling_exception = True

        if self.prev_ctx is None:
            # We're all by our lonesomes.

            # This means: PUSH the exception contexts on manually.
            self.push(exception.__traceback__)
            self.push(exception.__cause__)
            self.push(exception)

        # Try and move the exception.
        if self.exc_next_pointer:
            self.instruction_pointer = self.exc_next_pointer
        else:
            # Raise the exception instead.
            self.raise_exception(exception)

    def raise_exception(self, exception: BaseException):
        """
        Raises an exception to the previous function in the calling chain.

        This calls the on_exception_callback, and sets our state to ERRORED.

        This is called in one of two places:
            1) END_FINALLY is called with the exception state being None.
            2) safe_raise is called with the exception state being None.

        """
        self.state = VSCtxState.ERRORED

        if self._exception_callback:
            self._exception_callback(exception)


class VSWrappedFunction(object):
    """
    Represents a wrapped function.
    """

    def __init__(self, function: callable):
        self._f = function

    def __call__(self, *args, **kwargs):
        # Create a new Context and return it.
        ctx = _VSContext(self._f)
        ctx.fill_args(*args)

        return ctx
