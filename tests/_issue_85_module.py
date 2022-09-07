def forwardref_method(foo: "ForwardRef", bar: str) -> "ForwardRef":
    return ForwardRef(foo.x + bar)


class ForwardRef:
    def __init__(self, x="default"):
        self.x = x
