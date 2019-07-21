# -*- coding: utf-8 -*-


def _poseur_decorator(*poseur):
    """Positional-only arguments runtime checker.

    Args:
     - str, name of positional-only arguments

    Refs:
     - https://mail.python.org/pipermail/python-ideas/2017-February/044888.html

    """
    import functools
    def caller(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            poseur_args = set(poseur).intersection(kwargs)
            if poseur_args:
                raise TypeError('%s() got some positional-only arguments passed as keyword arguments: %r' %
                                (func.__name__, ', '.join(poseur_args)))
            return func(*args, **kwargs)
        return wrapper
    return caller


@_poseur_decorator('para_a', 'para_b')
def func_a(para_a, para_b, para_c, para_d, *, para_e, para_f):
    var_a = _poseur_decorator('p_a', 'p_b')(lambda p_a, p_b, p_c, p_d, *, p_e, p_f: (p_a, p_b, p_c, p_d, p_e, p_f))
    var_b = _poseur_decorator('p_a', 'p_b')(lambda p_a, p_b=1, p_c=2: p_a)

    @_poseur_decorator('p_a', 'p_b')
    def func_b(p_a, p_b=lambda pa, pb: (pa, pb), p_c=None):
        var_c = lambda p_a, p_b, *, p_c: p_c

    def func_c(p_a, p_b=_poseur_decorator('p_a')(lambda p_a=1: p_a)):
        pass


def func_d(p_a, p_b, *, p_c):
    var_b = _poseur_decorator('p_a', 'p_b')(lambda p_a, p_b=1, p_c=2: p_a)

    @_poseur_decorator('p_a', 'p_b')
    def func_e(p_a, p_b=lambda pa, pb: (pa, pb), p_c=None):
        var_c = lambda p_a, p_b, *, p_c: p_c

    def func_f(p_a, p_b=_poseur_decorator('p_a')(lambda p_a=1: p_a)):
        pass


def func_g(p_a, p_b=_poseur_decorator('p_a')(lambda p_a=1: p_a)):
    pass
