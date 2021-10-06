from abc import ABC
from typing import List

from kode.span import Span
from .tokens import OPERATOR_PRECEDENCE, Operator, PunctuationType, Reserved, TokenStream, ReservedType, Identifier, Punctuation, Literal
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
        if len(statements) == 0: raise Exception("Emtpy Statements.") 

        self.__statements = statements

    @property
    def span(self):
        span = None

        for statement in self.__statements:
            if span == None:
                span = statement.span
            else:
                span += statement.span

        if span == None:
            raise Exception("Statements without span.")

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
        if len(tokens) != 1: raise RuntimeWarning("Not single literal.")
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
        if len(tokens) != 1: raise RuntimeWarning("Not single identifier.")
        tokens.nxt(Identifier)

    @classmethod
    def parse(cls, tokens: TokenStream):
        return IdentifierStatement(tokens.pop())

    def __str__(self) -> str:
        return f"IdentifierStatement({self.__identifier})"

class Assignment(Statement):
    __span: Span
    __identifier: Identifier
    __statements: Statements

    def __init__(self, span: Span, identifier: Identifier, statements: Statements):
        self.__span = span
        self.__identifier = identifier
        self.__statements = statements

    @property
    def span(self):
        return self.__span + self.__identifier.span + self.__statements.span

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
        set_token = tokens.pop()
        identifier = tokens.pop()
        to_token = tokens.pop()
        statement_tokens = tokens.pop_until(Punctuation, True)
        statements = statementize(statement_tokens)
        if not tokens.empty(): tokens.pop()

        return Assignment(
            span=set_token.span + to_token.span, 
            identifier=identifier, 
            statements=statements
        )

    def __str__(self) -> str:
        return f"Assignment({self.__identifier},{self.__statements})"

    def __iter__(self):
        return self.__statements.__iter__()

class Operation(Statement):
    __span: Span
    __op_tree: any

    def __init__(self, span: Span, op_tree: any):
        self.__span = span
        self.__op_tree = op_tree

    @property
    def span(self):
        return self.__span

    @property
    def op_tree(self):
        return self.__op_tree

    @classmethod
    def istype(cls, tokens: TokenStream):
        while not tokens.empty():
            tokens.nxt([Identifier, Literal, Operator])

    @classmethod
    def __dp_parse(cls, operation: any):
        if len(operation) == 0: raise Exception("Invalid empty operand.")
        if len(operation) == 1: return operation[0]

        min_index = None
        min_precedence = float("inf")

        for i, value in enumerate(operation):
            if not type(value) == Operator: continue

            precedence = OPERATOR_PRECEDENCE[value.enum_type]

            if precedence <= min_precedence:
                min_index = i
                min_precedence = precedence

        lhs = operation[:min_index]
        operator = operation[min_index]
        rhs = operation[min_index + 1:]

        lhs = cls.__dp_parse(lhs)
        rhs = cls.__dp_parse(rhs)

        return (lhs, operator, rhs)

    @classmethod
    def parse(cls, tokens: TokenStream):
        span = None
        operation = []

        while not tokens.empty():
            token = tokens.pop()
            operation.append(token)

            if span == None:
                span = token.span
            else:
                span += token.span

        grouped_operation = []

        group = []
        for token in operation:
            if type(token) == Operator:
                grouped_operation.append(statementize(TokenStream(group)))
                grouped_operation.append(token)
                group = []
            else:
                group.append(token)

        if len(group) > 0:
            grouped_operation.append(statementize(TokenStream(group)))

        op_tree = cls.__dp_parse(grouped_operation)

        return Operation(
            span=span,
            op_tree=op_tree
        )

    def __str__(self) -> str:
        return f"Operation({self.op_tree})"

    def __repr__(self) -> str:
        return str(self)

class Show(Statement):
    __span: Span
    __statements: Statements

    def __init__(self, span: Span, statements: Statements):
        self.__span = span
        self.__statements = statements

    @property
    def span(self):
        return self.__span + self.__statements.span

    @property
    def statements(self) -> Statements:
        return self.__statements

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.SHOW)

    @classmethod
    def parse(cls, tokens: TokenStream):
        show = tokens.pop()
        statement_tokens = tokens.pop_until(PunctuationType.PERIOD, True)
        statements = statementize(statement_tokens)
        if not tokens.empty(): tokens.pop()

        return Show(show.span, statements)

    def __str__(self) -> str:
        return f"Show({self.__statements})"

    def __repr__(self) -> str:
        return str(self)

    def __iter__(self):
        return self.__statements.__iter__()

STATEMENT_TYPES = [
    LiteralStatement, 
    IdentifierStatement,
    Show,
    Assignment,
    Operation,
]

def statementize(tokens: TokenStream) -> Statements:
    statements = []

    while not tokens.empty():
        for StatementType in STATEMENT_TYPES:
            try:
                StatementType.istype(tokens.copy())
                statement = StatementType.parse(tokens)
                statements.append(statement)
                break
            except ParseError as err:
                raise err
            except RuntimeWarning as err:
                pass
            except Exception as err:
                raise err
        else:
            raise ParseError(span=tokens.span, message=f"Could not match any statement to tokens.")

    return Statements(statements)
