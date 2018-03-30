"""
Module provides named locks (inter process locks) to allow to decorate
functions with the lock. Decorating function directly with lock(path)
does not work as expected if path has to be taken from config object.
This is because the decorator is created during class/function
instantiation where the path should not be initialized yet. Before first
use of named lock, lock has to be set using set_lock(name, path). After
that, something like that can be used:

    @interprocess_lock(name)
    def guarded(...):
        ...

Where name stands for some str name.
"""
import fasteners
from functools import wraps

LOCKS = {}


def set_lock(name, path):
    LOCKS[name] = path


def _get_lock(name):
    return fasteners.InterProcessLock(LOCKS[name])


def interprocess_lock(name):
    def lock_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            with _get_lock(name):
                return f(*args, **kwargs)
        return wrapper
    return lock_decorator
