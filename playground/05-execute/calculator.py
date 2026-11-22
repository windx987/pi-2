"""A tiny calculator with one bug, for the execute exercise."""


def add(a, b):
    return a + b


def subtract(a, b):
    return a + b  # BUG: should be a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b
