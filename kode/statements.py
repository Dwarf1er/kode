from abc import ABC
from typing import List
from .tokens import OPERATOR_PRECEDENCE, TokenStream, ReservedType, Identifier, Punctuation, Reserved, Literal, OPERATORS
from .errors import ParseError

class Statement(ABC):
    @property
    def span(self):
        return None

    def __str__(self) -> str:
        return "Statement"

    def __repr__(self) -> str:
        return str(self)

class Statements(Statement):
    __statements: List[Statement]

    def __init__(self, statements: List[Statement]):
        self.__statements = statements

    @property
    def span(self):
        span = []

        for statement in self.__statements:
            span.append(statement.span)

        return span

    def __str__(self) -> str:
        return f"Statements({self.__statements})"

    def __iter__(self):
        return self.__statements.__iter__()

class LiteralStatement(Statement):
    __literal: Literal

    def __init__(self, literal: Literal):
        self.__literal = literal

    @property
    def span(self):
        return self.__literal.span

    @property
    def literal(self):
        return self.__literal

    @classmethod
    def istype(cls, tokens: TokenStream):
        if len(tokens) != 1: raise Exception("Not single literal.")
        tokens.nxt(Literal)

    @classmethod
    def parse(cls, tokens: TokenStream):
        return LiteralStatement(tokens.pop())

    def __str__(self) -> str:
        return f"LiteralStatement({self.__literal})"

class IdentifierStatement(Statement):
    __identifier: Identifier

    def __init__(self, identifier: Identifier):
        self.__identifier = identifier

    @property
    def span(self):
        return self.__identifier.span

    @property
    def identifier(self):
        return self.__identifier

    @classmethod
    def istype(cls, tokens: TokenStream):
        if len(tokens) != 1: raise Exception("Not single identifier.")
        tokens.nxt(Identifier)

    @classmethod
    def parse(cls, tokens: TokenStream):
        return IdentifierStatement(tokens.pop())

    def __str__(self) -> str:
        return f"IdentifierStatement({self.__identifier})"

class Assignment(Statement):
    __identifier: Identifier
    __statements: Statements

    def __init__(self, identifier: Identifier, statements: Statements):
        self.__identifier = identifier
        self.__statements = statements

    @property
    def span(self):
        return [self.__identifier.span] + self.__statements.span

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
    __lhs: Statement
    __operator: Reserved
    __rhs: Statement

    def __init__(self, lhs: Statement, operator: Reserved, rhs: Statement):
        self.__lhs = lhs
        self.__operator = operator
        self.__rhs = rhs

    @property
    def span(self):
        return self.__lhs.span + [self.__operator.span] + self.__rhs.span

    @property
    def lhs(self):
        return self.__lhs

    @property
    def operator(self):
        return self.__operator

    @property
    def rhs(self):
        return self.__rhs

    @classmethod
    def istype(cls, tokens: TokenStream):
        while not tokens.empty():
            tokens.nxt([Identifier, Literal] + OPERATORS)

    @classmethod
    def parse(cls, tokens: TokenStream):
        operation = []
        
        while not tokens.empty():
            operation.append(tokens.pop())

        max_index = -1
        max_precedence = -1

        for i, token in enumerate(operation):
            if not type(token) == Reserved: continue

            if token.rtype in OPERATOR_PRECEDENCE:
                precedence = OPERATOR_PRECEDENCE[token.rtype]

                if precedence >= max_precedence:
                    max_index = i
                    max_precedence = precedence

        lhs = operation[:max_index]
        operator = operation[max_index]
        rhs = operation[max_index+1:]

        lhs = statementize(TokenStream(lhs))
        rhs = statementize(TokenStream(rhs))

        return Operation(lhs=lhs, operator=operator, rhs=rhs)

    def __str__(self) -> str:
        return f"Operation({self.__lhs}, {self.__operator}, {self.__rhs})"

    def __repr__(self) -> str:
        return str(self)

class Show(Statement):
    __statements: Statements

    def __init__(self, statements: Statements):
        self.__statements = statements

    @property
    def span(self):
        return self.__statements.span

    @property
    def statements(self) -> Statements:
        return self.__statements

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.SHOW)

    @classmethod
    def parse(cls, tokens: TokenStream):
        tokens.pop()
        statement_tokens = tokens.pop_until(Punctuation, True)
        statements = statementize(statement_tokens)
        if not tokens.empty(): tokens.pop()

        return Show(statements)

    def __str__(self) -> str:
        return f"Show({self.__statements})"

    def __repr__(self) -> str:
        return str(self)

    def __iter__(self):
        return self.__statements.__iter__()

STATEMENT_TYPES = [
    LiteralStatement, 
    IdentifierStatement, 
    Assignment, 
    Operation, 
    Show
]

def statementize(tokens: TokenStream) -> Statements:
    statements = []

    while not tokens.empty():
        for StatementType in STATEMENT_TYPES:
            try:
                StatementType.istype(tokens.copy())
                # print(StatementType, tokens)
                statement = StatementType.parse(tokens)
                statements.append(statement)
                break
            except ParseError as err:
                raise err
            except Exception as err:
                pass
        else:
            raise ParseError(span=tokens.span, message=f"Could not match any statement to tokens.")

    return Statements(statements)
