from abc import ABC
from typing import List
from .tokens import TokenStream, ReservedType, Identifier, Token, Punctuation, Reserved, Literal, OPERATORS
from .errors import ParseError

class Statement(ABC):
    def __repr__(self) -> str:
        return str(self)

class Statements(Statement):
    __statements: List[Statement]

    def __init__(self, statements: List[Statement]):
        self.__statements = statements

    def __str__(self) -> str:
        return f"{self.__statements}"

    def __iter__(self):
        return self.__statements.__iter__()

class Assignment(Statement):
    __identifier: Identifier
    __statements: Statements

    def __init__(self, identifier: Identifier, statements: Statements):
        self.__identifier = identifier
        self.__statements = statements

    @property
    def statements(self) -> Statements:
        return self.__statements

    @property
    def identifier(self) -> Identifier:
        return self.__identifier

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.SET).nxt(Identifier).nxt(ReservedType.TO)

    @classmethod
    def parse(cls, tokens: TokenStream):
        tokens.pop()
        identifier = tokens.pop()
        tokens.pop()
        statement_tokens = tokens.pop_until(Punctuation, True)
        statements = statementize(statement_tokens)
        if not tokens.empty(): tokens.pop()

        return Assignment(identifier, statements)

    def __str__(self) -> str:
        return f"Assignment({self.__identifier},{self.__statements})"

    def __iter__(self):
        return self.__statements.__iter__()

class Operation(Statement):
    __operation: List[any]

    def __init__(self, operation: List[any]):
        self.__operation = operation

    @classmethod
    def istype(cls, tokens: TokenStream):
        while not tokens.empty():
            tokens.nxt([Identifier, Literal] + OPERATORS)

    @classmethod
    def parse(cls, tokens: TokenStream):
        operation = []
        
        while not tokens.empty():
            operation.append(tokens.pop())

        return Operation(operation)

    def __str__(self) -> str:
        return f"Operation({self.__operation})"

    def __repr__(self) -> str:
        return str(self)

    def __iter__(self):
        return self.__operation.__iter__()

class Tee(Statement):
    __statements: Statements

    def __init__(self, statements: Statements):
        self.__statements = statements

    @property
    def statements(self) -> Statements:
        return self.__statements

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.TEE)

    @classmethod
    def parse(cls, tokens: TokenStream):
        tokens.pop()
        statement_tokens = tokens.pop_until(Punctuation, True)
        statements = statementize(statement_tokens)
        if not tokens.empty(): tokens.pop()

        return Tee(statements)

    def __str__(self) -> str:
        return f"Tee({self.__statements})"

    def __repr__(self) -> str:
        return str(self)

    def __iter__(self):
        return self.__statements.__iter__()

STATEMENT_TYPES = [Assignment, Operation, Tee]

def statementize(tokens: TokenStream) -> Statements:
    statements = []

    while not tokens.empty():
        for StatementType in STATEMENT_TYPES:
            try:
                StatementType.istype(tokens.copy())
                statements.append(StatementType.parse(tokens))
                break
            except ParseError as err:
                raise err
            except Exception as err:
                pass
        else:
            raise ParseError(span=tokens.span, message=f"Could not match any statement to tokens.")

    return Statements(statements)
