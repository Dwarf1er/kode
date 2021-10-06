from abc import ABC
from enum import Enum, auto
from typing import Tuple, List
import re
from .span import Span
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
    INTEGER = auto()
    BOOLEAN = auto()
    FLOAT = auto()

def isfloat(value: str):
  try:
    float(value)
    return True
  except ValueError:
    return False

def isint(value: str):
    if value.startswith("-"):
        return value[1:].isdigit()
    else:
        return value.isdigit()

class Literal(Token):
    @property
    def value(self) -> any:
        ltype = self.ltype
        if ltype == LiteralType.STRING:
            return self.span.value[1:-1]
        elif ltype == LiteralType.INTEGER:
            return int(self.span.value)
        elif ltype == LiteralType.FLOAT:
            return float(self.span.value)
        elif ltype == LiteralType.BOOLEAN:
            return self.span.value.upper() == "TRUE"
        else:
            raise Exception("Unimplemented literal type.")

    @property
    def ltype(self) -> LiteralType:
        value = self.span.value

        if value[0] in STRING_DELIMITERS:
            return LiteralType.STRING
        elif isint(value):
            return LiteralType.INTEGER
        elif isfloat(value):
            return LiteralType.FLOAT
        elif value.upper() in ["TRUE", "FALSE"]:
            return LiteralType.BOOLEAN
        else:
            raise ParseError(self.span, f"Invalid literal type.")

    @classmethod
    def istype(cls, span: Span) -> bool:
        value = span.value

        if value[0] in STRING_DELIMITERS: return True
        if value == "-" or value.isdigit(): return True
        if value.upper() in ["TRUE", "FALSE"]: return True

        return False
    
    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Literal', int]:
        span = spans[0]

        if span.value == "-" or span.value.isdigit():
            i = 0

            for i, iter_span in enumerate(spans):
                if iter_span.value == "-":
                    if not i == 0:
                        break
                elif iter_span.value == ".":
                    if i >= len(spans) - 1: 
                        break
                    if not spans[i + 1].value.isdigit(): 
                        break
                elif iter_span.value.isdigit():
                    pass
                else:
                    break
            for iter_span in spans[:i]:
                span += iter_span

            return Literal(span), i

        if span.value[0] in STRING_DELIMITERS:
            string_terminator = span.value[0]

            for j, iter_span in enumerate(spans):
                if iter_span.value.endswith(string_terminator):
                    for inner_span in spans[:j+1]:
                        span += inner_span
                    return Literal(span), j+1
            else:
                raise ParseError(span, f"String not closed.")

        if span.value.upper() in ["TRUE", "FALSE"]:
            return Literal(span), 1

        raise ParseError(span, "Unknown literal type.")

    def __str__(self) -> str:
        try:
            return f"Literal({self.value},{self.ltype})"
        except:
            return f"Literal({self.span.value},ERROR)"

class ReservedType(Enum):
    IF = auto()
    IS = auto()
    TO = auto()
    THEN = auto()
    SET = auto()
    SHOW = auto()

class Reserved(Token):
    @property
    def enum_type(self) -> ReservedType:
        return ReservedType[self.value.upper()]

    @classmethod
    def istype(cls, span: Span) -> bool:
        return span.value.upper() in ReservedType._member_names_

    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Reserved', int]:
        span = spans[0]

        return Reserved(span), 1

    def __str__(self) -> str:
        return f"Reserved({self.enum_type})"

class OperatorType(Enum):
    PLUS = auto()
    MINUS = auto()
    TIMES = auto()
    DIVIDE = auto()
    MOD = auto()
    EQUALS = auto()

OPERATOR_PRECEDENCE = {
    OperatorType.MOD: 15,
    OperatorType.TIMES: 15,
    OperatorType.DIVIDE: 15,
    OperatorType.PLUS: 14,
    OperatorType.MINUS: 14,
    OperatorType.EQUALS: 11
}

class Operator(Token):
    @property
    def enum_type(self) -> OperatorType:
        return OperatorType[self.value.upper()]

    @classmethod
    def istype(cls, span: Span) -> bool:
        return span.value.upper() in OperatorType._member_names_

    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Operator', int]:
        span = spans[0]

        return Operator(span), 1

    def __str__(self) -> str:
        return f"Operator({self.enum_type})"

class Identifier(Token):
    def __str__(self) -> str:
        return f"Identifier({self.value})"

    @classmethod
    def istype(cls, span: Span) -> bool:
        return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", span.value)
    
    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Identifier', int]:
        span = spans[0]

        return Identifier(span), 1

class PunctuationType(Enum):
    PERIOD = "."
    MINUS = "-"

class Punctuation(Token):
    def __str__(self) -> str:
        return f"Punctuation({self.value})"

    @property
    def enum_type(self) -> PunctuationType:
        return PunctuationType(self.value)

    @classmethod
    def istype(cls, span: Span) -> bool:
        return span.value in [p.value for p in PunctuationType]

    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Punctuation', int]:
        return Punctuation(spans[0]), 1

TOKEN_TYPES = [
    Literal,
    Punctuation,
    Operator,
    Reserved,
    Literal,
    Identifier
]

class TokenStream:
    __tokens: List[Token]
    __ptr: int

    def __init__(self, tokens: List[Token], offset: int = 0):
        self.__tokens = tokens
        self.__ptr = offset
    
    @property
    def span(self) -> List[Span]:
        span = None

        for token in self.__tokens[self.__ptr:]:
            if span == None:
                span = token.span
            else:
                span += token.span
        
        return span

    def cnxt(self, value_types: any = None) -> bool:
        if self.__ptr >= len(self.__tokens): 
            raise Exception("Peek out of bound.")

        if not type(value_types) == list:
            value_types = [value_types]

        token = self.__tokens[self.__ptr]
        token_type = type(token)

        for value_type in value_types:
            if value_type == None: return True

            if issubclass(type(value_type), Enum):
                if not hasattr(token, 'enum_type'): continue
                if value_type == token.enum_type: return True
            else:
                if value_type == token_type: return True
        
        return False

    def nxt(self, value_type: any) -> 'TokenStream':
        if not self.cnxt(value_type): raise RuntimeWarning(value_type)

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
        return len(self) == 0

    def reset(self):
        self.__ptr = 0

    def __repr__(self) -> str:
        return str(self)

    def __len__(self):
        return max(len(self.__tokens) - self.__ptr, 0)

    def __str__(self) -> str:
        return f"TokenStream({self.__ptr},{self.__tokens})"

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
            raise ParseError(span, f"Unknown token type.")

    return TokenStream(tokens)
