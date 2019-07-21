# -*- coding: utf-8 -*-


def func_a(para_a, para_b, para_c, para_d, *, para_e, para_f):
    var_a = lambda p_a, p_b, /, p_c, p_d, *, p_e, p_f: (p_a, p_b, p_c, p_d, p_e, p_f)
    var_b = lambda p_a, p_b=1, /, p_c=2: p_a

    def func_b(p_a, p_b=lambda pa, pb: (pa, pb), /, p_c=None):
        var_c = lambda p_a, p_b, *, p_c: p_c

    def func_c(p_a, p_b=lambda p_a=1, /: p_a):
        pass


def func_d(p_a, p_b, *, p_c):
    var_b = lambda p_a, p_b=1, /, p_c=2: p_a

    def func_e(p_a, p_b=lambda pa, pb: (pa, pb), /, p_c=None):
        var_c = lambda p_a, p_b, *, p_c: p_c

    def func_f(p_a, p_b=lambda p_a=1, /: p_a):
        pass


def func_g(p_a, p_b=lambda p_a=1, /: p_a):
    pass
