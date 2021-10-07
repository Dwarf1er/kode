from kode.utils import print_span
from .statements import Conditional, IdentifierStatement, Input, LiteralStatement, Loop, Statement, Statements, Assignment, Operation, Show, statementize
from .tokens import Identifier, Literal, LiteralType, OperatorType, tokenize
from .span import Span, spanize
from .errors import ParseError, InterpreterError, handle_error
from typing import Dict, List
from abc import ABC

def get_literal(value: any, spanned_objects: list):
    if type(value) == Literal: raise RuntimeError("Passing a literal.")
    if type(value) == str: value = '"' + value + '"'

    spans: List[Span] = []

    for so in spanned_objects:
        if type(so) == Span:
            spans.append(so)
        else:
            spans.append(so.span)

    starts = [span.start for span in spans]
    ends = [span.end for span in spans]

    return Literal(
        Span(
            value=str(value),
            file_path=spans[0].file_path,
            start=min(starts),
            end=max(ends)
        )
    )

class Scope:
    __values: Dict[str, any]
    __depths: List[List[str]]

    def __init__(self):
        self.__values = {}
        self.__depths = [[]]

    def push(self):
        self.__depths.append([])

    def pop(self):
        if len(self.__depths) <= 1: return

        old_keys = self.__depths.pop()

        for key in old_keys:
            del self.__values[key]

    def put(self, key: Identifier, value: any):
        if not key.value in self.__values:
            self.__depths[-1].append(key.value)

        self.__values[key.value] = value

    def get(self, key: Identifier) -> any:
        if not key.value in self.__values: raise InterpreterError(key.span, "Variable not defined.")

        return self.__values[key.value]

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"Scope({self.__values},{self.__depths})"

class StatementInterpreter(ABC):
    _statement: Statement

    def __init__(self, statement: Statement):
        self._statement = statement

    def can_interpret(self) -> bool:
        return False

    def interpret(self, interpreter: 'Interpreter'):
        pass

class StatementsInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Statements

    def interpret(self, interpreter: 'Interpreter'):
        outputs = []
        spanned_objects = []

        for statement in self._statement:
            spanned_objects.append(statement)
            output = interpreter.run(statement)
            outputs.append(output)

        return outputs[-1]

class AssignmentInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Assignment

    def interpret(self, interpreter: 'Interpreter'):
        literal = interpreter.run(self._statement.statements)

        interpreter.scope.put(self._statement.identifier, literal.value)

        return literal + self._statement.span

class OperatorInterpreter(ABC):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return False

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return None

class PlusInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.PLUS

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value + rhs.value

class MinusInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.MINUS

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value - rhs.value

class TimesInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.TIMES

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value * rhs.value

class DivideInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.DIVIDE

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value // rhs.value

class ModInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.MOD

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value % rhs.value

class EqualsInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.EQUALS

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value == rhs.value 

class GreaterInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.GREATER

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value > rhs.value

class LessInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.LESS

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value < rhs.value

class AndInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.AND

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value and rhs.value

class OrInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.OR

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value or rhs.value

OPERATOR_INTERPRETERS = [
    PlusInterpreter,
    MinusInterpreter,
    TimesInterpreter,
    DivideInterpreter,
    ModInterpreter,
    EqualsInterpreter,
    GreaterInterpreter,
    LessInterpreter,
    AndInterpreter,
    OrInterpreter
]

class OperationInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Operation

    def __dp_interpret(self, op_tree: any, interpreter: 'Interpreter') -> Literal:
        if type(op_tree) == Statements: return interpreter.run(op_tree)

        lhs = self.__dp_interpret(op_tree[0], interpreter)
        rhs = self.__dp_interpret(op_tree[2], interpreter)

        operator: OperatorType = op_tree[1].enum_type

        for OP in OPERATOR_INTERPRETERS:
            if OP.can_interpret(operator):
                value = OP.interpret(lhs, rhs)

                return get_literal(value, spanned_objects=[lhs, rhs])
        else:
            raise InterpreterError(op_tree[1].span, "Unimplemented operator.")

    def interpret(self, interpreter: 'Interpreter') -> Literal:
        return self.__dp_interpret(self._statement.op_tree, interpreter)

class ShowInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Show

    def interpret(self, interpreter: 'Interpreter'):
        literal = interpreter.run(self._statement.statements)

        interpreter.display(literal.value)

        return literal + self._statement.span

class InputInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Input

    def interpret(self, interpreter: 'Interpreter'):
        value = interpreter.read()

        if value.isalpha():
            value = '"' + value + '"'

        span = self._statement.span
        span.value = value

        return Literal(span)

class LiteralInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == LiteralStatement

    def interpret(self, interpreter: 'Interpreter'):
        value = self._statement.literal.value

        return get_literal(value, spanned_objects=[self._statement])

class IdentifierInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == IdentifierStatement

    def interpret(self, interpreter: 'Interpreter'):
        value = interpreter.scope.get(self._statement.identifier)

        return get_literal(value, spanned_objects=[self._statement])

class ConditionalInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Conditional

    def interpret(self, interpreter: 'Interpreter'):
        interpreter.scope.push()

        literal = interpreter.run(self._statement.condition)

        if not literal.enum_type == LiteralType.BOOLEAN: raise InterpreterError(literal.span, "Conditional with a non-boolean.")

        if literal.value:
            return_literal = interpreter.run(self._statement.pass_statement)
        elif self._statement.fail_statement:
            return_literal = interpreter.run(self._statement.fail_statement)
        else:
            new_span = self._statement.span
            new_span.value = "None"

            interpreter.scope.pop()

            return Literal(new_span)

        interpreter.scope.pop()
        
        return return_literal + self._statement.span

class LoopInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Loop

    def interpret(self, interpreter: 'Interpreter'):
        interpreter.scope.push()

        last_value = None
        
        while True:
            literal = interpreter.run(self._statement.condition)

            if not literal.enum_type == LiteralType.BOOLEAN: raise InterpreterError(literal.span, "Loop with a non-boolean.")

            if literal.value == False: break

            last_value = interpreter.run(self._statement.statement)

        if last_value == None:
            new_span = self._statement.span
            new_span.value = "None"

            interpreter.scope.pop()

            return Literal(new_span)

        interpreter.scope.pop()

        return last_value + self._statement.span

STATEMENT_INTERPRETERS = [
    StatementsInterpreter,
    ConditionalInterpreter,
    LoopInterpreter,
    AssignmentInterpreter, 
    OperationInterpreter, 
    ShowInterpreter,
    LiteralInterpreter,
    IdentifierInterpreter,
    InputInterpreter
]

class Interpreter:
    __ast: Statements
    __stdout: str
    __silent: bool
    __debug: bool
    __scope: Scope

    def __init__(self, ast: Statements, silent: bool = False, debug: bool = False):
        self.__ast = ast
        self.__stdout = ""
        self.__silent = silent
        self.__debug = debug
        self.__scope = Scope()

    @property
    def scope(self):
        return self.__scope

    @property
    def stdout(self) -> str:
        return self.__stdout

    def read(self) -> str:
        # TODO: Not only input().
        return input()

    def display(self, line: str, terminator: str = "\n"):
        self.__stdout += str(line) + terminator

        if not self.__silent: print(line, end=terminator)

    def run(self, ast: Statement = None) -> Literal:
        if ast == None: ast = self.__ast

        for SI in STATEMENT_INTERPRETERS:
            si = SI(ast)

            if si.can_interpret():
                literal = si.interpret(self)

                if self.__debug:
                    print_span(literal.span)
                    print("|", "Value:", literal.value)
                    print("|")

                return literal

        raise InterpreterError(ast.span, "Cannot interpret statement.")

def parse(source: str, file_path: str) -> Statements:
    try:
        span = spanize(source, file_path)
        tokens = tokenize(span)
        ast = statementize(tokens)

        return ast
    except ParseError as err:
        handle_error(err)

def interpret(ast: Statements, debug: bool = False) -> any:
    try:
        interpeter = Interpreter(
            ast=ast,
            debug=debug
        )
        return interpeter.run()
    except InterpreterError as err:
        handle_error(err)
