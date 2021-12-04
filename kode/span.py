from typing import List

class Span:
    __start: int
    __end: int
    __value: str
    __file_path: str

    def __init__(self, value: str, file_path: str, start: int, end: int):
        self.__value = value
        self.__file_path = file_path
        self.__start = start
        self.__end = end

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, v: str):
        self.__value = v

    @property
    def file_path(self):
        return self.__file_path

    def pop(self, size: int = 1) -> 'Span':
        if size < 0: raise Exception("Cannot pop negative value.")
        if size > len(self.__value): raise Exception(f"Trying to pop greater than size.")

        pop_offset = self.__start
        self.__start += size
        pop_value, self.__value = self.__value[:size], self.__value[size:]

        return Span(
            value=pop_value, 
            file_path=self.__file_path,
            start=pop_offset,
            end=pop_offset + size
        )

    def __add__(self, other: 'Span'):
        if not type(other) == Span: raise Exception(f"Cannot add `{type(other)}` to Span.")

        new_start = min(self.start, other.start)
        new_end = max(self.end, other.end)

        new_size = len(self) + len(other) + abs(self.start - other.start)
        new_value = [" "] * new_size

        for i, c in enumerate(self.value, self.start - new_start):
            new_value[i] = c

        for i, c in enumerate(other.value, other.start - new_start):
            new_value[i] = c

        value = "".join(new_value).strip()

        return Span(
            value=value, 
            file_path=self.__file_path if self.__file_path else other.file_path,
            start=new_start,
            end=new_end    
        )

    def __iter__(self):
        return self.__value.__iter__()

    def __str__(self) -> str:
        return f"Span({self.value},{self.start}-{self.end})"

    def __repr__(self) -> str:
        return str(self)

    def __len__(self) -> int:
        return len(self.__value)

def spanize(source: str, file_path: str) -> List[Span]:
    from .tokens import PunctuationType

    source = Span(
        value=source, 
        file_path=file_path,
        start=0,
        end=len(source)
    )

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
