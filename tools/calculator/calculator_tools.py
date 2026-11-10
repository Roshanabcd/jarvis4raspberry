"""
JARVIS Deterministic Calculator Tools
Safe mathematical operations and arithmetic evaluation using Python.
"""
import ast
import math
import operator
import re
from typing import Any, Dict, Union

# Allowed operators for safe mathematical AST evaluation
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
}

_ALLOWED_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _eval_ast_node(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise TypeError(f"Unsupported constant type: {type(node.value)}")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](_eval_ast_node(node.operand))
        raise ValueError(f"Unsupported unary operator: {op_type}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            left = _eval_ast_node(node.left)
            right = _eval_ast_node(node.right)
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division by zero is undefined")
            # Limit power size to avoid DOS
            if op_type == ast.Pow and (right > 1000 or (isinstance(left, (int, float)) and abs(left) > 1000 and right > 10)):
                raise ValueError("Exponentiation result too large to compute safely")
            return _ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            if func_name in _ALLOWED_FUNCTIONS:
                args = [_eval_ast_node(arg) for arg in node.args]
                return _ALLOWED_FUNCTIONS[func_name](*args)
        raise ValueError(f"Unsupported function call in expression")

    if isinstance(node, ast.Name):
        name = node.id.lower()
        if name in _ALLOWED_CONSTANTS:
            return _ALLOWED_CONSTANTS[name]
        raise ValueError(f"Unsupported variable name: {name}")

    raise ValueError(f"Unsupported syntax: {type(node).__name__}")


def safe_eval_math(expr_str: str) -> Union[int, float]:
    """Parse and safely evaluate a mathematical expression without eval()."""
    clean_expr = expr_str.strip()
    # Strip conversational prefixes and trailing punctuation / instructions
    clean_expr = re.sub(r'^(?:what\s+is\s+|calculate\s+|compute\s+|solve\s+|how\s+much\s+is\s+|find\s+)', '', clean_expr, flags=re.I).strip()
    clean_expr = re.sub(r'\?.*$', '', clean_expr).strip()
    clean_expr = re.sub(r'\b(?:answer\s+in|please\s+answer|format|only)\b.*$', '', clean_expr, flags=re.I).strip().rstrip('?.')

    # Normalize natural language math terms
    clean_expr = re.sub(r'\bmultiplied\s+by\b', '*', clean_expr, flags=re.I)
    clean_expr = re.sub(r'\btimes\b', '*', clean_expr, flags=re.I)
    clean_expr = re.sub(r'\bdivided\s+by\b', '/', clean_expr, flags=re.I)
    clean_expr = re.sub(r'\bplus\b', '+', clean_expr, flags=re.I)
    clean_expr = re.sub(r'\bminus\b', '-', clean_expr, flags=re.I)
    clean_expr = re.sub(r'\bto\s+the\s+power\s+of\b', '**', clean_expr, flags=re.I)
    clean_expr = re.sub(r'\^', '**', clean_expr)

    # Handle "X percent of Y" -> (X / 100) * Y
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s+(?:of\s+)?(\d+(?:\.\d+)?)', clean_expr, flags=re.I)
    if pct_match:
        pct_val = float(pct_match.group(1))
        tot_val = float(pct_match.group(2))
        return (pct_val / 100.0) * tot_val

    parsed = ast.parse(clean_expr, mode='eval')
    val = _eval_ast_node(parsed.body)
    if isinstance(val, float) and val.is_integer():
        return int(val)
    return round(val, 6) if isinstance(val, float) else val


class CalculatorTools:
    """Production calculator tools with deterministic validation."""

    @staticmethod
    def add(a: float, b: float) -> Dict[str, Any]:
        """Add two numbers together."""
        res = a + b
        return {
            "operation": "add",
            "a": a,
            "b": b,
            "result": int(res) if isinstance(res, float) and res.is_integer() else res,
            "expression": f"{a} + {b} = {res}",
        }

    @staticmethod
    def subtract(a: float, b: float) -> Dict[str, Any]:
        """Subtract b from a."""
        res = a - b
        return {
            "operation": "subtract",
            "a": a,
            "b": b,
            "result": int(res) if isinstance(res, float) and res.is_integer() else res,
            "expression": f"{a} - {b} = {res}",
        }

    @staticmethod
    def multiply(a: float, b: float) -> Dict[str, Any]:
        """Multiply two numbers."""
        res = a * b
        return {
            "operation": "multiply",
            "a": a,
            "b": b,
            "result": int(res) if isinstance(res, float) and res.is_integer() else res,
            "expression": f"{a} * {b} = {res}",
        }

    @staticmethod
    def divide(a: float, b: float) -> Dict[str, Any]:
        """Divide a by b with ZeroDivisionError safety."""
        if b == 0:
            return {
                "operation": "divide",
                "a": a,
                "b": b,
                "error": "Division by zero is undefined.",
                "success": False,
            }
        res = a / b
        return {
            "operation": "divide",
            "a": a,
            "b": b,
            "result": int(res) if res.is_integer() else round(res, 6),
            "expression": f"{a} / {b} = {res}",
            "success": True,
        }

    @staticmethod
    def percentage(percent: float, total: float) -> Dict[str, Any]:
        """Calculate percentage of a total (e.g. 15% of 800 -> 120)."""
        res = (percent / 100.0) * total
        return {
            "operation": "percentage",
            "percent": percent,
            "total": total,
            "result": int(res) if isinstance(res, float) and res.is_integer() else round(res, 4),
            "expression": f"{percent}% of {total} = {res}",
            "success": True,
        }

    @staticmethod
    def calculate(expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expressions accurately and safely."""
        try:
            res = safe_eval_math(expression)
            return {
                "operation": "calculate",
                "expression": expression,
                "result": res,
                "success": True,
            }
        except ZeroDivisionError:
            return {
                "operation": "calculate",
                "expression": expression,
                "error": "Division by zero is undefined.",
                "success": False,
            }
        except Exception as e:
            return {
                "operation": "calculate",
                "expression": expression,
                "error": str(e),
                "success": False,
            }


calculator_tools = CalculatorTools()
