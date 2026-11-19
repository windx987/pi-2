# The arithmetic tool: evaluate_equation.
#
# Load all tools:  python3 -m pi2 -e tools
# Load only this:   python3 -m pi2 -e tools/math.py

import ast

from pi2 import ExtensionAPI, define_tool

MAX_EXPRESSION_LENGTH = 200
INF = float("inf")
NEG_INF = float("-inf")


def evaluate_ast(node):
    """Evaluate a safe arithmetic AST: numbers, +, -, *, /, unary signs and parentheses."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Only numbers are allowed in an expression.")
        return node.value

    if isinstance(node, ast.BinOp):
        left = evaluate_ast(node.left)
        right = evaluate_ast(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        raise ValueError("Only +, -, * and / are allowed in an expression.")

    if isinstance(node, ast.UnaryOp):
        value = evaluate_ast(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.USub):
            return -value
        raise ValueError("Only unary + and - are allowed in an expression.")

    raise ValueError("Only numbers, parentheses and +, -, *, / are allowed in an expression.")


def format_number(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def is_finite(value):
    """True for a real number, false for NaN and infinities."""
    return value == value and value not in (INF, NEG_INF)


def execute_evaluate_equation(params, ctx):
    expression = params["expression"].strip()
    if not expression:
        raise ValueError("expression is empty.")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError(f"expression is too long (limit {MAX_EXPRESSION_LENGTH} characters).")

    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as error:
        message = getattr(error, "msg", str(error))
        raise ValueError(f"Invalid expression: {message}.") from error

    try:
        result = evaluate_ast(tree.body)
    except ZeroDivisionError as error:
        raise ValueError("Cannot divide by zero.") from error
    except OverflowError as error:
        raise ValueError("The result is too large to compute.") from error

    if isinstance(result, float) and not is_finite(result):
        raise ValueError("The result is not a finite number.")
    return f"{expression} = {format_number(result)}"


evaluate_equation_tool = define_tool(
    name="evaluate_equation",
    label="evaluate_equation",
    description="Evaluate a basic arithmetic expression with +, -, *, / and parentheses.",
    prompt_snippet="Evaluate arithmetic expressions",
    prompt_guidelines=["Use evaluate_equation for arithmetic instead of guessing."],
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Arithmetic expression, for example '2 + 3 * 4'",
            },
        },
        "required": ["expression"],
    },
    execute=execute_evaluate_equation,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(evaluate_equation_tool)
