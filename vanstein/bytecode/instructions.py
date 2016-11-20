"""
Welcome to hell!

Each instruction takes two items: the dis.Instruction, and the _VSContext.
They are responsible for loading everything.
"""
import sys
try:
    import dis
    dis.Instruction
except AttributeError:
    from vanstein.backports import dis

from collections import Iterable

from vanstein.bytecode.vs_exceptions import safe_raise
from vanstein.context import _VSContext, VSCtxState, NO_RESULT
from vanstein.util import get_instruction_index_by_offset


def LOAD_GLOBAL(ctx: _VSContext, instruction: dis.Instruction):
    """
    Loads a global from `ctx.__globals__`.
    """
    name = ctx.co_names[instruction.arg]
    try:
        item = ctx.get_global(name)
    except KeyError:
        # todo: safe_raise
        return safe_raise(ctx, NameError("name '{}' is not defined".format(name)))

    ctx.push(item)
    return ctx


def LOAD_CONST(ctx: _VSContext, instruction: dis.Instruction):
    """
    Loads a const from `ctx.co_consts`.
    """
    ctx.push(ctx.co_consts[instruction.arg])
    return ctx


def LOAD_FAST(ctx: _VSContext, instruction: dis.Instruction):
    """
    Loads from VARNAMES.
    """
    item = ctx.varnames[instruction.arg]
    if item == NO_RESULT:
        safe_raise(ctx, NameError("name '{}' is not defined".format(ctx.co_varnames[instruction.arg])))
        return ctx
    ctx.push(item)
    return ctx


def POP_TOP(ctx: _VSContext, instruction: dis.Instruction):
    """
    Pops off the top of the stack.
    """
    ctx.pop()
    return ctx


def DUP_TOP(ctx: _VSContext, instruction: dis.Instruction):
    """
    Duplicates the top-most item on the stack.
    """
    item = ctx.pop()
    ctx.push(item)
    ctx.push(item)
    return ctx


def STORE_FAST(ctx: _VSContext, instruction: dis.Instruction):
    """
    Stores data in co_varnames.
    """
    ctx.varnames[instruction.arg] = ctx.pop()
    return ctx


def RETURN_VALUE(ctx: _VSContext, instruction: dis.Instruction):
    """
    Returns a value.

    This will set the state of the context.
    """
    ctx._result = ctx.pop()
    ctx.state = VSCtxState.FINISHED

    ctx._handling_exception = False

    return ctx


def COMPARE_OP(ctx: _VSContext, instruction: dis.Instruction):
    """
    Implements comparison operators.
    """
    # TODO: Rewrite COMPARE_OP into Vanstein-ran function calls.
    # TODO: Add all of the comparison functions.
    if instruction.arg == 10:
        # Pop the too match off.
        to_match = ctx.pop()
        # This is what we check.
        raised = ctx.pop()

        if not isinstance(to_match, Iterable):
            to_match = (to_match,)

        for e in to_match:
            # PyType_IsSubType
            if issubclass(type(raised), e):
                ctx.push(True)
                break
        else:
            ctx.push(False)

    return ctx


# region jumps
# Instructions that perform updating of the instruction pointer.

def JUMP_FORWARD(ctx: _VSContext, instruction: dis.Instruction):
    """
    Jumps forward to the specified instruction.
    """
    ctx.instruction_pointer = get_instruction_index_by_offset(ctx, instruction)

    return ctx


def POP_JUMP_IF_FALSE(ctx: _VSContext, instruction: dis.Instruction):
    """
    Jumps to the specified instruction if False-y is on the top of the stack.
    """
    i = ctx.pop()
    if i:
        # Truthy, don't jump.
        return ctx

    # Jump!
    ctx.instruction_pointer = get_instruction_index_by_offset(ctx, instruction)

    return ctx


def POP_JUMP_IF_TRUE(ctx: _VSContext, instruction: dis.Instruction):
    """
    Jumps to the specified instruction if True-y is on the top of the stack.
    """

    i = ctx.pop()
    if not i:
        # Falsey, stay where we are.
        return ctx

    # Jump, again.
    ctx.instruction_pointer = get_instruction_index_by_offset(ctx, instruction)

    return ctx


# endregion


# region Stubs
# Instructions that do nothing currently.

def POP_BLOCK(ctx: _VSContext, instruction: dis.Instruction):
    return ctx


# endregion

# region Exception handling
# Exception handling.
# These are all part of the Vanstein bootleg exception system.

def SETUP_EXCEPT(ctx: _VSContext, instruction: dis.Instruction):
    """
    Sets a context up for an except.
    """
    # Update the exception pointer with the calculated offset.
    # This is where we will jump to if an error is encountered.
    ctx.exc_next_pointer = get_instruction_index_by_offset(ctx, instruction)

    return ctx


def POP_EXCEPT(ctx: _VSContext, instruction: dis.Instruction):
    """
    Pops an except block.
    """
    # Here, we can make several assumptions:
    # 1) The exception has been handled.
    # 2) We can empty the exception state.
    # 3) The function can continue on as normal.

    # This means the exception state is cleared, handling_exception is removed, and it is safe to jump forward as
    # appropriate.
    ctx._exception_state = None
    ctx._handling_exception = False

    # Also, remove the exception pointer.
    # That way, it won't try to safely handle an exception that happens later on.
    ctx.exc_next_pointer = None

    return ctx


def RAISE_VARARGS(ctx: _VSContext, instruction: dis.Instruction):
    """
    Raises an exception to either the current scope or the outer scope.
    """
    # This is relatively simple.
    # We ignore the argc == 3, and pretend it's argc == 2
    argc = instruction.arg
    if argc == 3:
        # fuck you
        ctx.pop()
        argc = 2

    if argc == 2:
        # FROM exception is Top of stack now.
        fr = ctx.pop()
        # The real exception is top of stack now.
        exc = ctx.pop()
        exc.__cause__ = fr

    elif argc == 1:
        exc = ctx.pop()
    else:
        # Bare raise.
        exc = ctx._exception_state

    # Inject the exception.
    safe_raise(ctx, exc)
    # Raise the exception.

    return exc

# endregion
