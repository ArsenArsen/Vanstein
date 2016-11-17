"""
Welcome to hell!

Each instruction takes two items: the dis.Instruction, and the _VSContext.
They are responsible for loading everything.
"""
import dis

from vanstein.bytecode.vs_exceptions import safe_raise
from vanstein.context import _VSContext, VSCtxState


def LOAD_GLOBAL(ctx: _VSContext, instruction: dis.Instruction):
    """
    Loads a global from `ctx.__globals__`.
    """
    name = ctx.co_names[instruction.arg]
    try:
        item = ctx.get_global(name)
    except KeyError:
        # todo: safe_raise
        return safe_raise(ctx, NameError("name '{}' not defined".format(name)))

    ctx.push(item)
    return ctx


def LOAD_CONST(ctx: _VSContext, instruction: dis.Instruction):
    """
    Loads a const from `ctx.co_consts`.
    """
    ctx.push(ctx.co_consts[instruction.arg])
    return ctx


def LOAD_FAST(ctx: _VSContext, instruction: dis.Instruction):
    ctx.push(ctx.varnames[instruction.arg])
    return ctx


def POP_TOP(ctx: _VSContext, instruction: dis.Instruction):
    """
    Simple, this one.
    """
    ctx.pop()
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

    return ctx
