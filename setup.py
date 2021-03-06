from setuptools import setup, find_packages
import platform
import sys

if platform.python_implementation() != "CPython":
    raise SystemError("Vanstein only runs under CPython.")

if sys.version_info[0:2] < (3, 5):
    raise RuntimeError("Vanstein only runs on CPython 3.5 or above.")

import vanstein

setup(
    name='vanstein',
    version=vanstein.__version__,
    packages=find_packages(),
    url='https://github.com/SunDwarf/Vanstein',
    license='MIT',
    author='Isaac Dickinson',
    author_email='sun@veriny.tf',
    description='A Python 3.6+ implementation running on Python 3.3',
    install_requires=[
        "forbiddenfruit"
    ]
)
