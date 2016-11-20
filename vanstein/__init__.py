"""
How hacky.
"""
__version__ = "0.1.0"


def vanstein_sys_version(_=None):
    return "Vanstein", __version__, "async", None, None, "CPython"


def hijack():
    """
    Hijacks certain parts of code to make sure that they all return Vanstein built-ins.
    """
    import platform
    # Hijack platform._sys_version().
    platform._sys_version = vanstein_sys_version

    from vanstein.backports import apply_backports
    apply_backports()
