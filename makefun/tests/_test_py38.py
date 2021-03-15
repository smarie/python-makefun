def make_pos_only_f():
    def f(a, b, c, /, *, d, **e):
        return a + b + c + d + sum(e)
    return f
