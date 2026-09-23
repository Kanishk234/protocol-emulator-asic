"""Safe integer expressions for .trw files: numbers, names, + - * // % << >> & | ^ ~ and ( )."""

import ast
import operator

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.LShift: operator.lshift,
        ast.RShift: operator.rshift, ast.BitAnd: operator.and_, ast.BitOr: operator.or_,
        ast.BitXor: operator.xor, ast.Div: operator.truediv}
_UN = {ast.USub: operator.neg, ast.Invert: operator.invert, ast.UAdd: operator.pos}


class ExprError(Exception):
    pass


def evaluate(text, names):
    """Evaluate `text` with the given name -> value table. Ints stay ints; `/` gives a float."""
    try:
        tree = ast.parse(text.strip(), mode="eval")
    except SyntaxError as e:
        raise ExprError(f"bad expression {text!r}") from e

    def ev(node):
        if isinstance(node, ast.Expression):
            if isinstance(node.body, ast.Constant) and isinstance(node.body.value, str):
                return node.body.value               # a whole-expression string, e.g. "rise"
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in names:
                raise ExprError(f"unknown name {node.id!r} in {text!r}")
            return names[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            return _BIN[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
            return _UN[type(node.op)](ev(node.operand))
        raise ExprError(f"unsupported syntax in {text!r}")

    return ev(tree)
