"""
Welcome to hell!

Each instruction takes two items: the dis.Instruction, and the _VSContext.
They are responsible for loading everything.
"""
import dis

from vanstein.context import _VSContext


def POP_TOP(ctx: _VSContext, instruction: dis.Instruction):
    """
    Simple, this one.
    """
    ctx.pop()
    return ctx
