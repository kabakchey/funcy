from operator import __not__
from functools import partial, reduce

from .cross import map, imap
from ._inspect import get_spec
from .primitives import EMPTY
from .funcmakers import make_func


__all__ = ['identity', 'constantly', 'caller',
           'partial', 'rpartial', 'func_partial',
           'curry', 'rcurry', 'autocurry',
           'iffy',
           'compose', 'rcompose', 'complement', 'juxt', 'ijuxt']


def identity(x):
    """Returns its argument."""
    return x

def constantly(x):
    """Creates a function accepting any args, but always returning x."""
    return lambda *a, **kw: x

# an operator.methodcaller() brother
def caller(*a, **kw):
    """Creates a function calling its sole argument with given *a, **kw."""
    return lambda f: f(*a, **kw)

def func_partial(func, *args, **kwargs):
    """A functools.partial alternative, which returns a real function.
       Can be used to construct methods."""
    return lambda *a, **kw: func(*(args + a), **dict(kwargs, **kw))

def rpartial(func, *args):
    """Partially applies last arguments."""
    return lambda *a: func(*(a + args))


def curry(func, n=EMPTY):
    """Curries func into a chain of one argument functions."""
    if n is EMPTY:
        _, n, _ = get_spec(func)

    if n <= 1:
        return func
    elif n == 2:
        return lambda x: lambda y: func(x, y)
    else:
        return lambda x: curry(partial(func, x), n - 1)


def rcurry(func, n=EMPTY):
    """Curries func into a chain of one argument functions.
       Arguments are passed from right to left."""
    if n is EMPTY:
        _, n, _ = get_spec(func)

    if n <= 1:
        return func
    elif n == 2:
        return lambda x: lambda y: func(y, x)
    else:
        return lambda x: rcurry(rpartial(func, x), n - 1)


# TODO: drop `n` in next major release
def autocurry(func, n=EMPTY, _spec=None, _args=(), _kwargs={}):
    """Creates a version of func returning its partial applications
       until sufficient arguments are passed."""
    spec = _spec or (get_spec(func) if n is EMPTY else (set(), n, n))
    required_names, required_n, max_n = spec

    def autocurried(*a, **kw):
        args = _args + a
        kwargs = _kwargs.copy()
        kwargs.update(kw)

        if len(args) + len(kwargs) >= max_n:
            return func(*args, **kwargs)
        elif len(args) + len(set(kwargs) & required_names) >= required_n:
            try:
                return func(*args, **kwargs)
            except TypeError:
                return autocurry(func, _spec=spec, _args=args, _kwargs=kwargs)
        else:
            return autocurry(func, _spec=spec, _args=args, _kwargs=kwargs)

    return autocurried


def iffy(pred, action=EMPTY, default=identity):
    """Creates a function, which conditionally applies action or default."""
    if action is EMPTY:
        return iffy(bool, pred)
    else:
        return lambda v: action(v)  if pred(v) else           \
                         default(v) if callable(default) else \
                         default


def compose(*fs):
    """Composes passed functions."""
    if fs:
        pair = lambda f, g: lambda *a, **kw: f(g(*a, **kw))
        return reduce(pair, imap(make_func, fs))
    else:
        return identity

def rcompose(*fs):
    """Composes functions, calling them from left to right."""
    return compose(*reversed(fs))

def complement(pred):
    """Constructs a complementary predicate."""
    return compose(__not__, pred)


# NOTE: using lazy map in these two will result in empty list/iterator
#       from all calls to i?juxt result since map iterator will be depleted

def juxt(*fs):
    """Constructs a juxtaposition of the given functions.
       Result returns a list of results of fs."""
    extended_fs = map(make_func, fs)
    return lambda *a, **kw: [f(*a, **kw) for f in extended_fs]

def ijuxt(*fs):
    """Constructs a lazy juxtaposition of the given functions.
       Result returns an iterator of results of fs."""
    extended_fs = map(make_func, fs)
    return lambda *a, **kw: (f(*a, **kw) for f in extended_fs)
