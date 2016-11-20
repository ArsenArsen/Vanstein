"""
Miscellaneous utilities.
"""
import dis
import sys

from vanstein.context import _VSContext

PY36 = sys.version_info[0:2] >= (3, 6)


def get_instruction_index_by_offset(ctx: _VSContext, instruction: dis.Instruction) -> int:
    """
    Returns the index of an instruction (i.e ctx.instructions[I]) when given an offset to jump to.

    This is useful for when implementing an operator such as JUMP_FORWARD or SETUP_*.

    :param ctx: The context in which this is currently executing.
    :param instruction: The instruction to use.
    :return: The instruction index.
    """

    if PY36:
        # In CPython 3.6 and above, bytecode instructions are 2 bytes wide, all the time.
        # That means the offset can be divided by two and added to the instruction pointer.
        return ctx.instruction_pointer + (instruction.arg / 2)
    else:
        # This is a bit trickier.

        # However, we can use some known constants.
        # Opcodes with a code more than 90 have arguments, which means that they are length 3 (opcode + argv[0, 1])
        # We can loop over the instructions, check their opcode, and then check if the opcode is more than 90.
        # If it is, add 3 to our local raw pointer, because it has an argument, and 1 to the offset.
        # If it isn't, then only add 1 to our local raw pointer, but 1 to the offset again.
        # Once we've looped over these, we can then check if our local pointer is equal to the arg (NOT ARGVAL) of
        # the current instruction.
        # When it is, that means the instruction we're looking for is the current one, and we set the exception
        # pointer to our offset.

        # We have to special case arg = 1 on 3.5 and below.
        if instruction.arg == 1:
            return ctx.instruction_pointer + 1

        local_pointer = 0
        offset = 0
        for ins in ctx.instructions[ctx.instruction_pointer:]:
            if ins.opcode >= dis.HAVE_ARGUMENT:
                local_pointer += 3
            else:
                local_pointer += 1

            offset += 1

            if local_pointer == instruction.arg:
                # We've reached the right instruction.
                break
        else:
            raise SystemError("Could not find instruction at '{}'".format(instruction.argval))

        # The new instruction pointer is the current one + the offset we just calculated.
        return ctx.instruction_pointer + offset
