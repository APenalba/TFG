"""Comprensiones, expresiones generadoras y generadores."""


def evens(values):
    return [v for v in values if v % 2 == 0]


def index_pairs(rows):
    return {(i, j): x for i, row in enumerate(rows) for j, x in enumerate(row) if x and i != j}


def flatten(nested):
    return [item for sub in nested for item in sub]


def upper_triangle(n):
    return [[i * j for j in range(n) if j > i] for i in range(n)]


def unique_lengths(words):
    return {len(w) for w in words}


def total_positive(values):
    return sum(v for v in values if v > 0)


def countdown(n):
    while n > 0:
        yield n
        n -= 1


def chain(*iterables):
    for it in iterables:
        yield from it
