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

class Assignment(Statement):
    __identifier: Identifier
    __statement: Statement

    def __init__(self, identifier: Identifier, statement: Statement):
        self.__identifier = identifier
        self.__statement = statement

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.SET).nxt(Identifier).nxt(ReservedType.TO)

    @classmethod
    def parse(cls, tokens: TokenStream):
        tokens.pop()
        identifier = tokens.pop()
        tokens.pop()
        statement_tokens = tokens.pop_until(Punctuation, True)
        statement = statementize(statement_tokens)
        tokens.pop()

        return Assignment(identifier, statement)

    def __str__(self) -> str:
        return f"Assignment({self.__identifier},{self.__statement})"

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

STATEMENT_TYPES = [Assignment, Operation]

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
