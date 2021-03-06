from abc import ABC
from enum import Enum, auto
from typing import Tuple, List, Union
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
    NONE = auto()

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
        enum_type = self.enum_type

        if enum_type == LiteralType.STRING:
            return self.span.value[1:-1]
        elif enum_type == LiteralType.INTEGER:
            return int(self.span.value)
        elif enum_type == LiteralType.FLOAT:
            return float(self.span.value)
        elif enum_type == LiteralType.BOOLEAN:
            return self.span.value.upper() == "TRUE"
        elif enum_type == LiteralType.NONE:
            return None
        else:
            raise Exception("Unimplemented literal type.")

    @property
    def enum_type(self) -> LiteralType:
        value = self.span.value

        if len(value) == 0:
            return LiteralType.STRING
        elif value[0] in STRING_DELIMITERS:
            return LiteralType.STRING
        elif isint(value):
            return LiteralType.INTEGER
        elif isfloat(value):
            return LiteralType.FLOAT
        elif value.upper() in ["TRUE", "FALSE"]:
            return LiteralType.BOOLEAN
        elif value.upper() == "NONE":
            return LiteralType.NONE
        else:
            raise ParseError(self.span, f"Invalid literal type.")

    @classmethod
    def istype(cls, span: Span) -> bool:
        value = span.value

        if value[0] in STRING_DELIMITERS: return True
        if value == "-" or value.isdigit(): return True
        if value.upper() in ["TRUE", "FALSE"]: return True
        if value.upper() == "NONE": return True

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

        if span.value in STRING_DELIMITERS:
            string_terminator = span.value

            for j, iter_span in enumerate(spans[1:], 1):
                if iter_span.value == string_terminator:
                    for inner_span in spans[:j+1]:
                        span += inner_span
                    return Literal(span), j+1
            else:
                raise ParseError(span, f"String not closed.")

        if span.value.upper() in ["TRUE", "FALSE", "NONE"]:
            return Literal(span), 1

        raise ParseError(span, "Unknown literal type.")

    def __add__(self, other: Union[Span]) -> 'Literal':
        if type(other) == Span:
            return Literal(Span(
                value=self._span.value,
                file_path=self._span.file_path,
                start=min(self._span.start, other.start),
                end=max(self._span.end, other.end)
            ))
        else:
            raise Exception(f"Cannot add `{type(other)}` to Literal.")

    def __str__(self) -> str:
        try:
            return f"Literal({self.value},{self.enum_type})"
        except:
            return f"Literal({self.span.value},ERROR)"

class ReservedType(Enum):
    IF = auto()
    THEN = auto()
    ELSE = auto()

    WHILE = auto()
    DO = auto()

    END = auto()
    SET = auto()
    TO = auto()
    SHOW = auto()
    INPUT = auto()

END_BOUNDED_RESERVES = [ReservedType.IF, ReservedType.WHILE]

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
    GREATER = auto()
    LESS = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    BAND = auto()
    BOR = auto()
    SHL = auto() 
    SHR = auto()
    INDEX = auto()

OPERATOR_PRECEDENCE = {
    OperatorType.MOD: 15,
    OperatorType.TIMES: 15,
    OperatorType.DIVIDE: 15,
    OperatorType.PLUS: 14,
    OperatorType.MINUS: 14,
    OperatorType.EQUALS: 11,
    OperatorType.GREATER: 12,
    OperatorType.LESS: 12,
    OperatorType.AND: 7,
    OperatorType.OR: 6,
    OperatorType.XOR: 9,
    OperatorType.BAND: 10,
    OperatorType.BOR: 8,
    OperatorType.SHL: 13,
    OperatorType.SHR: 13,
    OperatorType.INDEX: 20
}

class Operator(Token):
    @property
    def enum_type(self) -> OperatorType:
        return OperatorType[self.value.upper()]

    @classmethod
    def istype(cls, span: Span) -> bool:
        if span.value.upper() in OperatorType._member_names_: return True

        return False

    @classmethod
    def parse(cls, spans: List[Span]) -> Tuple['Operator', int]:
        span = spans[0]
        i = 0

        if span.value.upper() in ["GREATER", "LESS"]:
            if not spans[1].value.isspace(): raise ParseError(spans[1], "Expected whitespace.")
            if not spans[2].value.upper() == "THAN": raise ParseError(spans[2], "Expected THAN.")

            new_span = span + spans[1] + spans[2]
            new_span.value = span.value
            span = new_span 

            i += 2

        return Operator(span), i + 1

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
    DOUBLE_QUOTE = '"'
    QUOTE = "'"

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
    Identifier
]

class TokenStream:
    __tokens: List[Token]
    __ptr: int

    def __init__(self, tokens: List[Token] = None, offset: int = 0):
        if tokens == None:
            self.__tokens = []
        else:
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

    def cnxt(self, value_types: any = None, offset: int = 0) -> bool:
        if self.__ptr >= len(self.__tokens): 
            raise Exception("Peek out of bound.")

        if not type(value_types) == list:
            value_types = [value_types]

        token = self.__tokens[self.__ptr + offset]
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

        if self.empty() and not includes_end:
            if len(tokens) == 0:
                spans = Span("", "", 0, 0)
            else:
                spans = tokens[0].span

                for token in tokens[1:]:
                    spans += token.span

                raise ParseError(spans, "Could not parse token stream.")

        return TokenStream(tokens)

    def copy(self) -> 'TokenStream':
        return TokenStream(self.__tokens, self.__ptr)

    def empty(self) -> bool:
        return len(self) == 0

    def reset(self):
        self.__ptr = 0

    def __add__(self, other: Union[Token, 'TokenStream']) -> 'TokenStream':
        if issubclass(type(other), Token):
            return TokenStream(self.__tokens + [other], self.__ptr)
        elif issubclass(type(other), TokenStream):
            return TokenStream(self.__tokens + other.__tokens, self.__ptr)
        else:
            raise Exception(f"Cannot add `{type(other)}` to TokenStream.")

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
