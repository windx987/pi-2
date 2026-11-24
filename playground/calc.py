# Small library the workshop agent reads, edits and tests. `average` has a bug on purpose.


def add(a, b):
    return a + b


def average(values):
    total = 0
    for value in values:
        total = add(total, value)
    return total / (len(values) - 1)
