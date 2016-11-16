# Backported modules.

import sys

import dis as _original_dis
from . import dis


def apply_backports():
    """
    Applies backports to `sys.modules`.
    """
    sys.modules["_original_dis"] = _original_dis
    # Hijack `dis` with our backported dis.
    # Of course, on Python 3.6+, dis has changed.
    # So we can't use it there.
    if sys.version_info[0:2] < (3, 6):
        sys.modules["dis"] = dis
