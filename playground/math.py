# The workshop playground: one small bug. Run it with `python3 math.py`.
# The tools change the return line and check the result through the agent.

def add(a, b):
    return a - b  # BUG: should be a + b


if __name__ == "__main__":
    result = add(2, 3)
    assert result == 5, f"add(2, 3) returned {result}, expected 5"
    print("ok")
