"""
Test A: Testing Vanstein.

This is to ensure the loop and the bytecode engine works properly, not to test it in all scenarios.
"""
import vanstein
from vanstein.decorators import async_func, native_invoke

vanstein.hijack()

from vanstein.loop import BaseAsyncLoop
import pytest


@pytest.fixture
def vs_loop():
    """
    A fixture that creates a Vanstein event loop each test.
    """
    return BaseAsyncLoop()


# BEGIN TESTS
def test_basic_return(vs_loop: BaseAsyncLoop):
    # Tests a basic RETURN_VALUE function.
    @async_func
    def a():
        return 1

    assert vs_loop.run(a()) == 1


def test_load_store_fast(vs_loop: BaseAsyncLoop):
    # Tests LOAD_FAST/STORE_FAST
    @async_func
    def a():
        x = 1
        return x

    assert vs_loop.run(a()) == 1


# We can't use closures here, so define some functions.

@native_invoke
def b1(): return 2


@async_func
def b2(): return 2


def b3(): return 3


@async_func
def a1(): return b1()


@async_func
def a2(): return b2()


@async_func
def a3(): return b3()


def test_call_native_function(vs_loop: BaseAsyncLoop):
    # Tests calling a function with native_invoke.
    # This is separate to the calling a real function test.

    assert vs_loop.run(a1()) == 2


def test_call_function(vs_loop: BaseAsyncLoop):
    # Tests calling some regular functions.
    assert vs_loop.run(a2()) == 2
    assert vs_loop.run(a3()) == 3
