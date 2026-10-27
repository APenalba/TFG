"""Funciones anidadas, decoradores, lambdas y código asíncrono."""

import functools

double = lambda x: x * 2  # noqa: E731


def logged(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("quiet"):
            return func(*args)
        return func(*args, **kwargs)

    return wrapper


def retry(times):
    def decorator(func):
        def wrapper(*args):
            for _ in range(times):
                try:
                    return func(*args)
                except OSError:
                    continue
            return None

        return wrapper

    return decorator


@logged
def greet(name, quiet=False):
    return "hi " + name


@retry(3)
def fetch(url):
    return url


def make_counter():
    count = 0

    def increment(step=1):
        nonlocal count
        if step > 0:
            count += step
        return count

    return increment


def sort_by_key(items):
    return sorted(items, key=lambda item: item[1] or item[0])


async def produce(queue, n):
    for i in range(n):
        await queue.put(i)


async def consume(source, lock):
    results = []
    async for item in source:
        if item is None:
            break
        results.append(item)
    async with lock:
        results.sort()
    return results
