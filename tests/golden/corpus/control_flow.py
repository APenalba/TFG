"""Flujo de control: ramas, bucles, excepciones y operadores booleanos."""


def identity(value):
    return value


def classify(n):
    if n < 0:
        return "negative"
    elif n == 0:
        return "zero"
    elif n < 10:
        return "small"
    else:
        return "large"


def sum_until(limit, values):
    total = 0
    for v in values:
        if v > limit:
            break
        total += v
    else:
        total = -total
    i = 0
    while i < limit:
        i += 1
    return total + i


def find_pair(matrix, target):
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value == target:
                return i, j
            if value is None:
                continue
    return None


def safe_div(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        result = 0
    except (TypeError, ValueError) as exc:
        raise RuntimeError("bad input") from exc
    else:
        result += 1
    finally:
        pass
    return result


def read_first(path):
    with open(path, encoding="utf-8") as handle:
        line = handle.readline()
    if not line:
        raise ValueError("empty file")
    return line.strip()


def check(a, b, c):
    if a and b or c:
        return True
    return not (a or b or c)


def sign_of(x):
    return "positive" if x > 0 else "non-positive"


def require_positive(x):
    assert x > 0, "x must be positive"
    return x


def dispatch(command):
    match command:
        case "start":
            return 1
        case "stop" | "halt":
            return 2
        case _:
            return 0
