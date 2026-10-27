"""Clases con atributos, métodos y herencia."""

import math
from abc import ABC, abstractmethod


class Shape(ABC):
    """Figura abstracta."""

    count = 0

    def __init__(self, name):
        self.name = name
        Shape.count += 1

    @abstractmethod
    def area(self):
        raise NotImplementedError

    def describe(self):
        return f"{self.name}: {self.area():.2f}"


class Circle(Shape):
    def __init__(self, radius):
        super().__init__("circle")
        self.radius = radius

    def area(self):
        return math.pi * self.radius**2

    @property
    def diameter(self):
        return self.radius * 2


class Rectangle(Shape):
    def __init__(self, width, height):
        super().__init__("rectangle")
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def is_square(self):
        return self.width == self.height and self.width > 0

    @classmethod
    def square(cls, side):
        return cls(side, side)

    @staticmethod
    def from_pair(pair):
        if len(pair) != 2:
            raise ValueError("expected two values")
        return Rectangle(*pair)


class Square(Rectangle):
    def __init__(self, side):
        super().__init__(side, side)


class Inventory:
    def __init__(self):
        self.items = []
        self.log = []

    def add(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def record(self, message):
        self.log.append(message)


def total_area(shapes):
    return sum(s.area() for s in shapes if isinstance(s, Shape))
