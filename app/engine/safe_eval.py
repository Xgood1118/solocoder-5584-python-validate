import ast
import operator
from datetime import datetime
from typing import Any, Dict, Optional


class SafeExpressionEvaluator:
    _BINARY_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.BitAnd: operator.and_,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
    }

    _UNARY_OPS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
        ast.Invert: operator.invert,
    }

    _COMPARE_OPS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
    }

    _BOOL_OPS = {
        ast.And: all,
        ast.Or: any,
    }

    _SAFE_FUNCTIONS = {
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'round': round,
        'datetime': datetime,
    }

    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        self._variables = variables or {}

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        elif isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Name):
            if node.id in self._variables:
                return self._variables[node.id]
            elif node.id in self._SAFE_FUNCTIONS:
                return self._SAFE_FUNCTIONS[node.id]
            else:
                raise NameError(f"Name '{node.id}' is not defined")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type in self._BINARY_OPS:
                return self._BINARY_OPS[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in self._UNARY_OPS:
                return self._UNARY_OPS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

        elif isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type not in self._BOOL_OPS:
                raise ValueError(f"Unsupported boolean operator: {op_type.__name__}")
            values = [self._eval_node(v) for v in node.values]
            return self._BOOL_OPS[op_type](values)

        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_type = type(op)
                if op_type in self._COMPARE_OPS:
                    if not self._COMPARE_OPS[op_type](left, right):
                        result = False
                        break
                    left = right
                else:
                    raise ValueError(f"Unsupported comparison operator: {op_type.__name__}")
            return result

        elif isinstance(node, ast.IfExp):
            test = self._eval_node(node.test)
            if test:
                return self._eval_node(node.body)
            else:
                return self._eval_node(node.orelse)

        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            if not callable(func) or not self._is_safe_callable(func):
                raise ValueError("Unsupported function call")
            args = [self._eval_node(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
            return func(*args, **kwargs)

        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            if isinstance(node.slice, ast.Slice):
                lower = self._eval_node(node.slice.lower) if node.slice.lower else None
                upper = self._eval_node(node.slice.upper) if node.slice.upper else None
                step = self._eval_node(node.slice.step) if node.slice.step else None
                return value[lower:upper:step]
            else:
                slice_val = self._eval_node(node.slice)
                return value[slice_val]

        elif isinstance(node, ast.Attribute):
            value = self._eval_node(node.value)
            return getattr(value, node.attr)

        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            elements = [self._eval_node(elt) for elt in node.elts]
            if isinstance(node, ast.Tuple):
                return tuple(elements)
            elif isinstance(node, ast.Set):
                return set(elements)
            return elements

        elif isinstance(node, ast.Dict):
            keys = [self._eval_node(k) for k in node.keys if k is not None]
            values = [self._eval_node(v) for v in node.values]
            return dict(zip(keys, values))

        else:
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")

    def _is_safe_callable(self, func) -> bool:
        if func in self._SAFE_FUNCTIONS.values():
            return True
        if isinstance(func, type) and issubclass(func, (str, int, float, bool)):
            return True
        return False

    @classmethod
    def evaluate(cls, expression: str, variables: Optional[Dict[str, Any]] = None) -> Any:
        if not expression or not isinstance(expression, str):
            raise ValueError("Empty or invalid expression")

        if len(expression) > 2048:
            raise ValueError("Expression too long")

        tree = ast.parse(expression, mode='eval')

        if cls._has_unsafe_nodes(tree):
            raise ValueError("Unsafe expression detected")

        evaluator = cls(variables=variables)
        return evaluator._eval_node(tree)

    @classmethod
    def _has_unsafe_nodes(cls, tree: ast.AST) -> bool:
        unsafe_types = (
            ast.Lambda,
            ast.GeneratorExp,
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.Await,
            ast.Yield,
            ast.YieldFrom,
            ast.Assign,
            ast.AugAssign,
            ast.AnnAssign,
            ast.Delete,
            ast.Import,
            ast.ImportFrom,
            ast.Global,
            ast.Nonlocal,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.With,
            ast.Raise,
            ast.Try,
            ast.Assert,
            ast.Starred,
            ast.NamedExpr,
        )
        for node in ast.walk(tree):
            if isinstance(node, unsafe_types):
                return True
            if isinstance(node, ast.Name) and node.id.startswith('_'):
                return True
        return False
