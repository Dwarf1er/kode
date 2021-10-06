from typing import List

class Span:
    __offset: int
    __value: str
    __file_path: str

    def __init__(self, value: str, file_path: str, offset: int = 0):
        self.__offset = offset
        self.__value = value
        self.__file_path = file_path

    @property
    def offset(self):
        return self.__offset

    @property
    def end(self):
        return self.__offset + len(self.__value)

    @property
    def value(self):
        return self.__value

    @property
    def file_path(self):
        return self.__file_path

    def pop(self, size: int = 1) -> 'Span':
        if size < 0: raise Exception("Cannot pop negative value.")
        if size > len(self.__value): raise Exception(f"Trying to pop greater than size.")

        pop_offset = self.offset
        self.__offset += size
        pop_value, self.__value = self.__value[:size], self.__value[size:]

        return Span(pop_value, file_path=self.__file_path, offset=pop_offset)

    def __add__(self, other: 'Span'):
        if not type(other) == Span: raise Exception(f"Cannot add non-Span to Span.")

        min_span = self if self.offset < other.offset else other
        max_span = self if not min_span == self else other

        if min_span.end < max_span.offset - 1: raise Exception(f"{self} and {other} do not intersect.")

        if min_span.end >= max_span.end:
            value = min_span.value
        else:
            value = min_span.value[:max_span.offset] + max_span.value

        return Span(value, file_path=self.__file_path, offset=min_span.offset)

    def __iter__(self):
        return self.__value.__iter__()

    def __str__(self) -> str:
        return f"Span({self.value},{self.offset})"

    def __repr__(self) -> str:
        return str(self)

    def __len__(self) -> int:
        return len(self.__value)

def spanize(source: str, file_path: str) -> List[Span]:
    from .tokens import PunctuationType

    source = Span(source, file_path=file_path)
    spans = []

    i = 0
    is_space = source.value[0].isspace()
    while i < len(source):
        c = source.value[i]

        if c in [p.value for p in PunctuationType]:
            spans.append(source.pop(i))
            spans.append(source.pop())
            if len(source.value) > 0:
                is_space = source.value[0].isspace()
            else:
                is_space = False
            i = 0
        elif c.isspace():
            if not is_space:
                spans.append(source.pop(i))
                is_space = True
                i = 0
        elif is_space:
            spans.append(source.pop(i))
            is_space = False
            i = 0

        i += 1

    if len(source) > 0:
        spans.append(source)

    return spans
