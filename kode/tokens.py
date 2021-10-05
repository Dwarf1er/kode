from abc import ABC
from enum import Enum, auto
from typing import Tuple, List
import re
from .utils import isnumber, Span
from .errors import ParseError

class Token(ABC):
    _span: Span

    def __init__(self, span: Span):
        self._span = span

    @property
    def value(self) -> any:
        return self.span.value

    @property
    def span(self) -> Span:
        return self._span

    def __repr__(self) -> str:
        return str(self)

STRING_DELIMITERS = ["'", '"']

class LiteralType(Enum):
    STRING = auto()
    NUMBER = auto()

class Literal(Token):
    @property
    def value(self) -> any:
        if self.ltype == LiteralType.STRING:
            return self.span.value[1:-1]
        else:
            return self.span.value

    @property
    def ltype(self) -> LiteralType:
        if self.span.value[0] in STRING_DELIMITERS:
            return LiteralType.STRING
        elif isnumber(self.span.value):
            return LiteralType.NUMBER
        else:
            raise ParseError(self.span, f"Invalid literal type.")

    @classmethod
    def istype(cls, span: Span) -> bool:
        if span.value[0] in STRING_DELIMITERS: return True
        if isnumber(span.value): return True

        return False
    
    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Literal', int]:
        span = spans[0]

        if isnumber(span.value):
            return Literal(span), 1

        if span.value[0] in STRING_DELIMITERS:
            tt = span.value[0]

            for j, ns in enumerate(spans):
                if ns.value.endswith(tt):
                    for nss in spans[:j+1]:
                        span = span + nss
                    return Literal(span), j+1
            else:
                raise ParseError(span, f"String not closed.")

    def __str__(self) -> str:
        return f"Literal({self.value},{self.ltype})"

class ReservedType(Enum):
    IF = auto()
    IS = auto()
    TO = auto()
    THEN = auto()
    SET = auto()
    PLUS = auto()
    MINUS = auto()
    SHOW = auto()

OPERATORS = [ReservedType.PLUS, ReservedType.MINUS]

class Reserved(Token):
    @property
    def rtype(self) -> ReservedType:
        return ReservedType[self.value.upper()]

    @classmethod
    def istype(cls, span: Span) -> bool:
        return span.value.upper() in ReservedType._member_names_

    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Reserved', int]:
        return Reserved(spans[0]), 1

    def __str__(self) -> str:
        return f"Reserved({self.rtype})"

class Identifier(Token):
    def __str__(self) -> str:
        return f"Identifier({self.value})"

    @classmethod
    def istype(cls, span: Span) -> bool:
        return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", span.value)
    
    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Identifier', int]:
        return Identifier(spans[0]), 1

class PunctuationType(Enum):
    Period = "."

class Punctuation(Token):
    def __str__(self) -> str:
        return f"Punctuation({self.value})"

    @classmethod
    def istype(cls, span: Span) -> bool:
        return span.value in [p.value for p in PunctuationType]

    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Punctuation', int]:
        return Punctuation(spans[0]), 1

TOKEN_TYPES = [Punctuation, Literal, Reserved, Literal, Identifier]

class TokenStream:
    __tokens: List[Token]
    __ptr: int

    def __init__(self, tokens: List[Token], offset: int = 0):
        self.__tokens = tokens
        self.__ptr = offset
    
    @property
    def span(self) -> List[Span]:
        return [token.span for token in self.__tokens[self.__ptr:]]

    def cnxt(self, value_types: any = None) -> bool:
        if self.__ptr >= len(self.__tokens): raise Exception("Peek out of bound.")

        if not type(value_types) == list:
            value_types = [value_types]

        for value_type in value_types:
            if value_type == None: return True

            token = self.__tokens[self.__ptr]
            token_type = type(token)
            
            if type(value_type) == ReservedType and token_type == Reserved:
                if token.rtype == value_type: return True
            elif type(value_type) == LiteralType and token_type == Literal:
                if token.ltype == value_type: return True
            elif value_type == token_type: return True
        
        return False

    def nxt(self, value_type: any) -> 'TokenStream':
        if not self.cnxt(value_type): raise Exception(value_type)

        self.__ptr += 1

        return self

    def pop(self) -> Token:
        token = self.__tokens[self.__ptr]

        self.__ptr += 1

        return token

    def peek(self) -> Token:
        return self.__tokens[self.__ptr]

    def pop_until(self, value_type: any, includes_end: bool = False) -> 'TokenStream':
        tokens = []

        while not self.empty() and not self.cnxt(value_type):
            tokens.append(self.pop())

        if self.empty() and not includes_end: raise IndexError()

        return TokenStream(tokens)

    def copy(self) -> 'TokenStream':
        return TokenStream(self.__tokens, self.__ptr)

    def empty(self) -> bool:
        return self.__ptr >= len(self.__tokens)

    def reset(self):
        self.__ptr = 0

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"TokenStream({self.__ptr},{self.__tokens})"

def spanize(source: str) -> List[Span]:
    source = Span(source)
    spans = []

    i = 0
    is_space = source.value[0].isspace()
    while i < len(source):
        c = source.value[i]

        if c in [p.value for p in PunctuationType]:
            spans.append(source.pop(i))
            is_space = False
            i = 0
        elif c.isspace():
            if not is_space:
                is_space = True
                spans.append(source.pop(i))
                i = 0
        elif is_space:
            is_space = False
            spans.append(source.pop(i))
            i = 0

        i += 1

    if len(source) > 0:
        spans.append(source)

    return spans

def tokenize(spans: List[Span]) -> TokenStream:
    tokens = []
    i = 0

    while i < len(spans):
        span = spans[i]
        
        if span.value.isspace():
            i += 1
            continue

        for TokenType in TOKEN_TYPES:
            if TokenType.istype(span):
                token, offset = TokenType.parse(spans[i:])
                tokens.append(token)
                i += offset
                break
        else:
            raise ParseError(span, f"Invalid token type.")

    return TokenStream(tokens)
