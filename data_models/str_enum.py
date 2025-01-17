from enum import Enum
from typing import Iterator, Type, TypeVar

T = TypeVar("T")


class StrEnum(str, Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.value!r}"

    @classmethod
    def __iter__(cls: Type[T]) -> Iterator[T]:
        for i in cls:
            yield cls(i)
