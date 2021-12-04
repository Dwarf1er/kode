from kode.utils import print_span
from .statements import Conditional, IdentifierStatement, Input, LiteralStatement, Loop, Statement, Statements, Assignment, Operation, Show, statementize
from .tokens import Identifier, Literal, LiteralType, OperatorType, tokenize
from .span import Span, spanize
from .errors import ParseError, InterpreterError, handle_error
from typing import Dict, List, Callable
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
        if not key.value in self.__values: raise InterpreterError(key.span, f"Variable {key.value} not defined.")

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

        if len(outputs) == 0:
            return Literal(Span(value="", file_path=None, start=0, end=0))
        else:
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
        if lhs.enum_type == LiteralType.STRING:
            return lhs.value + str(rhs.value)
        elif lhs.enum_type == LiteralType.FLOAT:
            return lhs.value + float(rhs.value)
        elif lhs.enum_type == LiteralType.INTEGER:
            return lhs.value + int(rhs.value)
        else:
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
        if lhs.enum_type == LiteralType.NONE and rhs.enum_type == LiteralType.NONE:
            return True

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

class BorInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.BOR

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value | rhs.value

class BandInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.BAND

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value & rhs.value

class XorInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.XOR

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value ^ rhs.value

class ShlInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.SHL

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value << rhs.value

class ShrInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.SHR

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        return lhs.value >> rhs.value

class IndexInterpreter(OperatorInterpreter):
    @classmethod
    def can_interpret(cls, operator: OperatorType) -> bool:
        return operator == OperatorType.INDEX

    @classmethod
    def interpret(cls, lhs: Literal, rhs: Literal) -> any:
        if not lhs.enum_type in [LiteralType.STRING]:
            raise InterpreterError(lhs.span, f"Cannot index {lhs.enum_type}.")

        if not rhs.enum_type in [LiteralType.INTEGER]:
            raise InterpreterError(rhs.span, f"Cannot index with {rhs.enum_type}.")

        return lhs.value[rhs.value]

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
    OrInterpreter,
    BandInterpreter,
    BorInterpreter,
    XorInterpreter,
    ShlInterpreter,
    ShrInterpreter,
    IndexInterpreter
]

class OperationInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Operation

    def interpret(self, interpreter: 'Interpreter') -> Literal:
        lhs = interpreter.run(self._statement.lhs)
        rhs = interpreter.run(self._statement.rhs)

        operator: OperatorType = self._statement.operator.enum_type

        for OP in OPERATOR_INTERPRETERS:
            if OP.can_interpret(operator):
                value = OP.interpret(lhs, rhs)

                return get_literal(value, spanned_objects=[lhs, rhs])
        else:
            raise InterpreterError(op_tree[1].span, f"Unimplemented operator {operator}.")

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
        
        # TODO: Maybe we want this behaviour?
        # if value == None:
            # raise InterpreterError(self._statement.span, "Could not get input.")

        if not value:
            value = "None"
        elif value.isalpha():
            value = '"' + value + '"'

        span = self._statement.span
        span.value = value

        return Literal(span)

class LiteralInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == LiteralStatement

    def interpret(self, interpreter: 'Interpreter'):
        literal = self._statement.literal

        return literal + self._statement.span

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

        if not literal.enum_type == LiteralType.BOOLEAN: 
            raise InterpreterError(literal.span, f"Cannot perform conditional with {literal.enum_type}.")

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

            if not literal.enum_type == LiteralType.BOOLEAN: raise InterpreterError(literal.span, f"Cannot perform loop conditional with {literal.enum_type}.")

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
    __input_method: Callable[[], str]

    def __init__(self, ast: Statements, silent: bool = False, debug: bool = False, input_method: Callable[[], str] = input):
        self.__ast = ast
        self.__stdout = ""
        self.__silent = silent
        self.__debug = debug
        self.__scope = Scope()
        self.__input_method = input_method

    @property
    def scope(self):
        return self.__scope

    @property
    def stdout(self) -> str:
        return self.__stdout

    def read(self) -> str:
        return self.__input_method()

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
