# -*- coding: utf-8 -*-


def func_a(para_a, para_b, para_c, para_d, *, para_e, para_f):
    var_a = lambda p_a, p_b, p_c, p_d, *, p_e, p_f: (p_a, p_b, p_c, p_d, p_e, p_f)
    var_b = lambda p_a, p_b=1, p_c=2: (p_a, p_b, p_c)

    print('var_a:', var_a('a', 'b', 'c', p_d='d', p_e='e', p_f='f'))
    print('var_b:', var_b('a'))

    def func_b(p_a, p_b=lambda pa, pb: (pa, pb), p_c=None):
        var_c = lambda p_a, p_b, *, p_c: (p_c, p_b, p_c)
        print('var_c:', var_c(1, p_b=2, p_c=3))
        return p_a, p_b('a', 'b'), p_c

    def func_c(p_a, p_b=lambda p_a=1: p_a):
        return p_a, p_b()

    print('func_b:', func_b('p_a'))
    print('func_c:', func_c('p_a'))

    return para_a, para_b, para_c, para_d, para_e, para_f


def func_d(p_a, p_b, *, p_c):
    var_b = lambda p_a, p_b=1, p_c=2: (p_a, p_b, p_c)
    print('var_b:', var_b('a'))

    def func_e(p_a, p_b=lambda pa, pb: (pa, pb), p_c=None):
        var_c = lambda p_a, p_b, *, p_c: (p_c, p_b, p_c)
        print('var_c:', var_c(1, p_b=2, p_c=3))
        return p_a, p_b('a', 'b'), p_c

    def func_f(p_a, p_b=lambda p_a=1: p_a):
        return p_a, p_b()

    print('func_e:', func_e('p_a'))
    print('func_f:', func_f('p_a'))

    return p_a, p_b, p_c


def func_g(p_a, p_b=lambda p_a=1: p_a):
    return p_a, p_b()


if __name__ == '__main__':
    print('func_a:', func_a('a', 'b', 'c', 'd', para_e='e', para_f='f'))
    print('func_d:', func_d('a', p_b='b', p_c='c'))
    print('func_g:', func_g('a'))
