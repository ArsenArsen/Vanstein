"""
The main "event" loop.

The way the Vanstein event loop works:

 1) Decompile a specified function
 2) Run the bytecode instruction-by-instruction
 3) When a function call is detected:
   3a) If it's builtin, call it.
   3b) If it's not, switch out of the current function context.
       The new function context will be added to the end of the call stack, which will wake up the previous
       function's context.
       Then the loop will pluck the top-most function from the top of the deque, and run it.
"""
import dis
import os
import traceback
import warnings
from collections import deque

import time

import sys

from vanstein.bytecode.engine import VansteinEngine
from vanstein.context import _VSContext, VSCtxState
from vanstein.decorators import native_invoke


class BaseAsyncLoop(object):
    """
    The basic async loop.

    This implements everything that is required.
    """
    def __init__(self):
        self._closed = False

        self._running = False

        # This deque stores the tasks that are currently running.
        # They are popped from the left and added to the right.
        self.running_tasks = deque()

        # This is the current bytecode engine.
        # This is used to run the actual bytecode used by VS.
        self.bytecode_engine = VansteinEngine()

    # Note: Nearly all functions inside the loop are native-invoke.
    # Why? Because running a copy of VS inside VS is a horribly wrong process.
    # As such, attempts to run this inside itself will be met with failure, and will just natively invoke.

    @native_invoke
    def _start_execution(self, context: _VSContext):
        """Begins execution of a task."""
        new_ctx = self.bytecode_engine.run_context(context)

        # Misuse by reference passing.
        if new_ctx is not None:
            # Add it to the end of the deque.
            self.running_tasks.append(new_ctx)
            # Add the old task, too.
            self.running_tasks.append(context)
            return

        # Check the return value of the current context.
        if context.state is VSCtxState.FINISHED:
            # Disappear the context.
            return
        elif context.state in [VSCtxState.SUSPENDED, VSCtxState.PENDING]:
            # Add it to the end of the deque again.
            self.running_tasks.append(context)
        elif context.state is VSCtxState.ERRORED:
            pass
        else:
            warnings.warn("Caught running context - this is not good!")
            self.running_tasks.append(context)

    @native_invoke
    def _step(self):
        """
        Moves one step forward in the event loop.

        This will collect the next task from the deque, and run it.

        This is an internal function and should not be called.
        """
        if not self._running:
            raise RuntimeError("Loop is not running.")

        if not self.running_tasks:
            # TODO: Handle loop wind-down.
            return

        next_task = self.running_tasks.popleft()
        assert isinstance(next_task, _VSContext)
        if next_task.state is VSCtxState.SUSPENDED:
            # It hasn't reached a wake-up call yet, so re-add it to the end of the deque.
            self.running_tasks.append(next_task)
            return

        if next_task.state == VSCtxState.RUNNING:
            # No need to use safe_raise here.
            # This will never raise a VS-handled exception, because it's a native invoke function.
            raise RuntimeError("Current task state is RUNNING - this should never happen!")

        if next_task.state is VSCtxState.PENDING:
            # It's newly created, or otherwise ready. Continue execution.
            # This should automatically pop or push it as appropriate.
            try:
                return self._start_execution(next_task)
            except NotImplementedError as e:
                print("Fatal error in Vanstein:")
                print("Instruction '{}' is not implemented yet.".format(
                    self.bytecode_engine.current_instruction.opname))
                print("Function disassembly:")
                dis.dis(next_task)
                print("Current context: {}".format(self.bytecode_engine.current_context))
                print("Current instruction: {}".format(self.bytecode_engine.current_instruction))
                raise
            except BaseException as e:
                print("Fatal error in Vanstein:")
                traceback.print_exc(file=sys.stdout)
                print("Function disassembly:")
                dis.dis(next_task)
                print("Current context: {}".format(self.bytecode_engine.current_context))
                print("Current instruction: {}".format(self.bytecode_engine.current_instruction))
                raise

        if next_task.state is VSCtxState.FINISHED:
            # Hopefully, we never have to see this.
            warnings.warn("Reached FINISHED task in event loop...")
            return next_task

    @native_invoke
    def run_forever(self):
        """
        Runs the event loop forever.
        """
        while self.running_tasks:
            self._step()

            # TODO: Check events.

    @native_invoke
    def run(self, function: _VSContext):
        """
        The main entry point into the event loop.

        This will begin running your context.
        """
        if self._running:
            raise RuntimeError("Loop is already running")
        if self._closed:
            raise RuntimeError("Loop is closed")
        # Place it onto the task queue.
        self.running_tasks.append(function)

        self._running = True

        # We still have a reference, so run_forever.
        try:
            self.run_forever()
        finally:
            self._running = False

        if function.state is VSCtxState.ERRORED:
            raise function._exception_state

        if function.state is VSCtxState.RUNNING:
            raise RuntimeError("Context {} never completed".format(function))

        # If we can, return the result of the function.
        return function.result
