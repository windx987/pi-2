# The math tool: evaluate_equation.

import ast
import operator

from pi2 import ExtensionAPI, define_tool

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def evaluate(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp):
        value = evaluate(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise ValueError("Only unary + and - are allowed.")
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](evaluate(node.left), evaluate(node.right))
    raise ValueError("Only numbers, parentheses and +, -, *, / are allowed.")


def execute(params, ctx):
    expression = params["expression"].strip()
    if not expression:
        raise ValueError("expression is empty.")
    try:
        result = evaluate(ast.parse(expression, mode="eval").body)
    except SyntaxError as error:
        raise ValueError(f"Invalid expression: {error.msg}") from error
    except ZeroDivisionError as error:
        raise ValueError("Cannot divide by zero.") from error
    return f"{expression} = {result:g}"


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
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(evaluate_equation_tool)
