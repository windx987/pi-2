# One small bug. Run it with `python3 math.py`.
# The exercise asks the agent to fix the return line with the `edit` tool.


def add(a, b):
    return a - b  # BUG: should be a + b


if __name__ == "__main__":
    result = add(2, 3)
    assert result == 5, f"add(2, 3) returned {result}, expected 5"
    print("ok")
