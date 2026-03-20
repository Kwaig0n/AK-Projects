"""Safe arithmetic calculator for financial calculations."""
import ast
import operator

CALCULATOR_TOOL_DEF = {
    "name": "calculate",
    "description": (
        "Perform financial or mathematical calculations. "
        "Use for: monthly mortgage repayments, stamp duty estimates, rental yield, "
        "ROI, compound interest, or any other number-crunching."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": (
                    "Math expression to evaluate. "
                    "Examples: '750000 * 0.06 / 12' (monthly interest), "
                    "'(650 * 52) / 750000 * 100' (rental yield %)"
                ),
            },
            "description": {
                "type": "string",
                "description": "What this calculation represents, e.g. 'Monthly mortgage repayment at 6%'",
            },
        },
        "required": ["expression"],
    },
}

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_eval_node(node.operand))
    else:
        raise ValueError(f"Unsupported operation in expression")


async def calculate(expression: str, description: str = "") -> dict:
    """Safely evaluate a math expression — no arbitrary code execution."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_node(tree.body)
        return {
            "result": round(result, 4),
            "expression": expression,
            "description": description or "Calculation result",
        }
    except ZeroDivisionError:
        return {"error": "Division by zero", "expression": expression}
    except Exception as e:
        return {"error": f"Invalid expression: {e}", "expression": expression}
