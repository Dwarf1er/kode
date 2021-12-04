from abc import ABC
from typing import List

from kode.span import Span
from .tokens import END_BOUNDED_RESERVES, OPERATOR_PRECEDENCE, Operator, PunctuationType, Token, TokenStream, ReservedType, Identifier, Punctuation, Literal
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
        if len(self.__statements) == 0:
            return Span(value="", file_path=None, start=0, end=0)

        span = None

        for statement in self.__statements:
            if span == None:
                span = statement.span
            else:
                span += statement.span

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

    def __str__(self) -> str:
        return f"LiteralStatement({self.__literal})"

    @classmethod
    def istype(cls, tokens: TokenStream):
        if len(tokens) != 1: raise RuntimeWarning("Not single literal.")
        tokens.nxt(Literal)

    @classmethod
    def parse(cls, tokens: TokenStream):
        return LiteralStatement(tokens.pop())

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

    def __str__(self) -> str:
        return f"IdentifierStatement({self.__identifier})"

    @classmethod
    def istype(cls, tokens: TokenStream):
        if len(tokens) != 1: raise RuntimeWarning("Not single identifier.")
        tokens.nxt(Identifier)

    @classmethod
    def parse(cls, tokens: TokenStream):
        return IdentifierStatement(tokens.pop())

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

    def __str__(self) -> str:
        return f"Assignment({self.__identifier},{self.__statements})"

    def __iter__(self):
        return self.__statements.__iter__()

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

class Operation(Statement):
    __lhs: Statement
    __operator: Operator
    __rhs: Statement

    def __init__(self, lhs: Statement, operator: Operator, rhs: Statement):
        self.__lhs = lhs
        self.__operator = operator
        self.__rhs = rhs

    @property
    def span(self):
        return self.__lhs.span + self.__operator.span + self.__rhs.span

    @property
    def lhs(self):
        return self.__lhs

    @property
    def operator(self):
        return self.__operator

    @property
    def rhs(self):
        return self.__rhs

    def __str__(self) -> str:
        return f"Operation({self.__lhs},{self.__operator},{self.__rhs})"

    @classmethod
    def istype(cls, tokens: TokenStream):
        while not tokens.empty():
            tokens.nxt([Identifier, Literal, Operator])

    @classmethod
    def parse(cls, tokens: TokenStream):
        operation = []

        while not tokens.empty():
            token = tokens.pop()
            operation.append(token)

        min_index = None
        min_precedence = float("inf")

        for i, value in enumerate(operation):
            if not type(value) == Operator: continue

            precedence = OPERATOR_PRECEDENCE[value.enum_type]

            if precedence <= min_precedence:
                min_index = i
                min_precedence = precedence

        lhs = statementize(TokenStream(operation[:min_index]))
        operator = operation[min_index]
        rhs = statementize(TokenStream(operation[min_index+1:]))

        return Operation(
            lhs=lhs,
            operator=operator,
            rhs=rhs
        )

class Show(Statement):
    __span: Span
    __statements: Statements

    def __init__(self, span: Span, statements: Statements):
        self.__span = span
        self.__statements = statements

    @property
    def span(self):
        return self.__span + self.__statements.span

    def __str__(self) -> str:
        return f"Show({self.__statements})"

    def __iter__(self):
        return self.__statements.__iter__()

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

class Input(Statement):
    __span: Span

    def __init__(self, span: Span):
        self.__span = span

    @property
    def span(self):
        return self.__span

    def __str__(self) -> str:
        return f"Input"

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.INPUT)

    @classmethod
    def parse(cls, tokens: TokenStream):
        input_token = tokens.pop()

        return Input(input_token.span)

class Conditional(Statement):
    __span: Span
    __condition: Statement
    __pass_statement: Statement
    __fail_statement: Statement

    def __init__(self, span: Span, condition: Statement, pass_statement: Statement, fail_statement: Statement):
        self.__span = span
        self.__condition = condition
        self.__pass_statement = pass_statement
        self.__fail_statement = fail_statement

    @property
    def span(self):
        span = self.__span + self.__condition.span + self.__pass_statement.span

        if self.__fail_statement:
            span += self.__fail_statement.span

        return span

    @property
    def condition(self):
        return self.__condition

    @property
    def pass_statement(self):
        return self.__pass_statement

    @property
    def fail_statement(self):
        return self.__fail_statement

    def __str__(self) -> str:
        return f"Conditional({self.__condition}, {self.__pass_statement}, {self.__fail_statement})"

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.IF)

    @classmethod
    def parse(cls, tokens: TokenStream):
        if_token = tokens.pop()
        condition_body = tokens.pop_until(ReservedType.THEN)
        then_token = tokens.pop()

        pass_body = TokenStream()
        fail_body = TokenStream()

        else_token = None
        end_token = None

        end_count = 1
        while not tokens.empty():
            for ebr in END_BOUNDED_RESERVES:
                if tokens.cnxt(ebr):
                    end_count += 1
                    break

            if tokens.cnxt(ReservedType.END):
                end_count -= 1

                if end_count < 0:
                    raise ParseError(tokens.pop(), "End count is negative.")

                if end_count == 0:
                    end_token = tokens.pop()
                    break

            if end_count == 1 and tokens.cnxt(ReservedType.ELSE):
                if not else_token:
                    else_token = tokens.pop()
                    continue

                raise ParseError(tokens.peek().span, "Too many else.")

            if else_token:
                fail_body += tokens.pop()
            else:
                pass_body += tokens.pop()
        else:
            raise ParseError(if_token.span + then_token.span + pass_body.span + fail_body.span, "Conditional statement is not closed.")

        span = if_token.span + then_token.span + end_token.span

        if else_token:
            span += else_token.span

        condition = statementize(condition_body)
        pass_statement = statementize(pass_body)

        if fail_body:
            fail_statement = statementize(fail_body)
        else:
            fail_statement = None

        return Conditional(
            span=span,
            condition=condition,
            pass_statement=pass_statement,
            fail_statement=fail_statement
        )

class Loop(Statement):
    __span: Span
    __condition: Statement
    __statement: Statement

    def __init__(self, span: Span, condition: Statement, statement: Statement):
        self.__span = span
        self.__condition = condition
        self.__statement = statement
    
    @property
    def span(self):
        return self.__span + self.__condition.span + self.__statement.span

    @property
    def condition(self):
        return self.__condition

    @property
    def statement(self):
        return self.__statement

    def __str__(self) -> str:
        return f"Loop({self.__condition}, {self.__statement})"

    @classmethod
    def istype(cls, tokens: TokenStream):
        tokens.nxt(ReservedType.WHILE)

    @classmethod
    def parse(cls, tokens: TokenStream):
        while_token = tokens.pop()
        condition_body = tokens.pop_until(ReservedType.DO)
        do_token = tokens.pop()

        body = TokenStream()
        end_token = None

        end_count = 1
        while not tokens.empty():
            for ebr in END_BOUNDED_RESERVES:
                if tokens.cnxt(ebr):
                    end_count += 1
                    break

            if tokens.cnxt(ReservedType.END):
                end_count -= 1

                if end_count == 0:
                    end_token = tokens.pop()
                    break
            
            body += tokens.pop()
        else:
            raise ParseError(while_token.span, "Unable to parse loop statement.")

        span = while_token.span + do_token.span + end_token.span
        condition = statementize(condition_body)
        statement = statementize(body)

        return Loop(
            span=span,
            condition=condition,
            statement=statement
        )

STATEMENT_TYPES = [
    LiteralStatement, 
    IdentifierStatement,
    Conditional,
    Loop,
    Show,
    Assignment,
    Input,
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
    
    if len(statements) == 1:
        return statements[0]
    else:
        return Statements(statements)
