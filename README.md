## Vanstein

**Vanstein** is an async implementation of Python 3.6 running inside CPython 3.3 or above.  

It runs using CPython 3.3+ bytecode structures and emulates the entirety of CPython, providing a nearly seamless translation layer
between your code and the real implementation.

### Dependencies

 - CPython 3.3 or higher
    This means no alternative implementations.
 - `forbiddenfruit` for patching certain built-ins
 - `enum34` if running on CPython lower than 3.4
 
### Installation

To install the latest version of Vanstein:

```bash
$ pip install -U vanstein
```

To install the latest development version of Vanstein:

```bash
$ pip install -U git+https://github.com/SunDwarf/Vanstein.git
```

### Getting started

Vanstein sits transparently between CPython and your code, automatically turning it async when you run it.  
Very little modification is required.

```py
import vanstein
from vanstein.decorators import async_func

# This call is essential!
vanstein.hijack()

import my.code

# It is recommended that you create an entry point instead of running
# your code directly.

@async_func
def entry_point(*args):
    return my.code.run(*args)
    
loop = vanstein.get_event_loop()
sys.exit(loop.run(entry_point(*sys.argv)))
```

### FAQ

**NotImplementedError: \<opcode\>**

This means your code is using a CPython feature that isn't currently supported inside Vanstein.  
Either upgrade, or wait for the feature to be implemented. Vanstein aims to be a 1<->1 replication of CPython.

**AttributeError: 'module' object has no attribute 'Instruction'**

This means you forgot to run `vanstein.hijack()`. This function call is very important, as it replaces certain
parts of the CPython runtime to make things work more seamlessly.
