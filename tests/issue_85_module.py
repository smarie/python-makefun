from dataclasses import dataclass


def forwardref_method(foo: "ForwardRef", bar: str) -> "ForwardRef":
    return foo.x + bar


@dataclass
class ForwardRef:
    x: str = "default"
