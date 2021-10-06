from .statements import IdentifierStatement, LiteralStatement, Statement, Statements, Assignment, Operation, Show, statementize
from .tokens import ReservedType, tokenize
from .span import spanize
from .errors import ParseError, InterpreterError, handle_error
from typing import Dict, List
from abc import ABC

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

    def put(self, key: str, value: any):
        if not key in self.__values:
            self.__depths[-1].append(key)

        self.__values[key] = value

    def get(self, key: str) -> any:
        return self.__values[key]

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

        for statement in self._statement:
            output = interpreter.run(statement)
            outputs.append(output)

        return outputs

class AssignmentInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Assignment

    def interpret(self, interpreter: 'Interpreter'):
        value = interpreter.run(self._statement.statements)[-1]

        interpreter.scope.put(self._statement.identifier.value, value)

        return value

class OperationInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Operation

    def __dp_interpret(self, op_tree: any, interpreter: 'Interpreter'):
        if type(op_tree) == Statements: return interpreter.run(op_tree)[-1]

        lhs = self.__dp_interpret(op_tree[0], interpreter)
        rhs = self.__dp_interpret(op_tree[2], interpreter)

        operator: ReservedType = op_tree[1].rtype

        if operator == ReservedType.PLUS:
            return lhs + rhs
        elif operator == ReservedType.MINUS:
            return lhs - rhs
        elif operator == ReservedType.TIMES:
            return lhs * rhs
        elif operator == ReservedType.DIVIDE:
            # TODO: Check int and float?
            return lhs // rhs
        elif operator == ReservedType.MOD:
            return lhs % rhs
        elif operator == ReservedType.EQUALS:
            return lhs == rhs
        else:
            raise InterpreterError(self._statement.operator, "Unimplemented operator.")

    def interpret(self, interpreter: 'Interpreter'):
        return self.__dp_interpret(self._statement.op_tree, interpreter)

class ShowInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == Show

    def interpret(self, interpreter: 'Interpreter'):
        value = interpreter.run(self._statement.statements)[-1]

        interpreter.display(value)

        return value

class LiteralInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == LiteralStatement

    def interpret(self, interpreter: 'Interpreter'):
        return self._statement.literal.value

class IdentifierInterpreter(StatementInterpreter):
    def can_interpret(self) -> bool:
        return type(self._statement) == IdentifierStatement

    def interpret(self, interpreter: 'Interpreter'):
        return interpreter.scope.get(self._statement.identifier.value)

STATEMENT_INTERPRETERS = [
    StatementsInterpreter, 
    AssignmentInterpreter, 
    OperationInterpreter, 
    ShowInterpreter,
    LiteralInterpreter,
    IdentifierInterpreter
]

class Interpreter:
    __ast: Statements
    __stdout: str
    __silent: bool
    __scope: Scope

    def __init__(self, ast: Statements, silent: bool = False):
        self.__ast = ast
        self.__stdout = ""
        self.__silent = silent
        self.__scope = Scope()

    @property
    def scope(self):
        return self.__scope

    @property
    def stdout(self) -> str:
        return self.__stdout

    def display(self, line: str, terminator: str = "\n"):
        self.__stdout += str(line) + terminator

        if not self.__silent: print(line, end=terminator)

    def run(self, ast: Statement = None) -> List[any]:
        if ast == None: ast = self.__ast

        for SI in STATEMENT_INTERPRETERS:
            si = SI(ast)

            if si.can_interpret():
                return si.interpret(self)

        raise InterpreterError(ast.span, "Cannot interpret statement.")

def parse(source: str, file_path: str) -> Statements:
    try:
        span = spanize(source, file_path)
        tokens = tokenize(span)
        ast = statementize(tokens)

        return ast
    except ParseError as err:
        handle_error(err)

def interpret(ast: Statements) -> any:
    try:
        interpeter = Interpreter(ast)
        return interpeter.run()[-1]
    except InterpreterError as err:
        handle_error(err)
