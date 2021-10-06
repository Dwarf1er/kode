from .statements import Statements, Assignment, Operation, Show, statementize
from .tokens import Literal, LiteralType, ReservedType, Reserved, Identifier, tokenize
from .span import spanize
from .errors import ParseError, InterpreterError, handle_error
from typing import Dict, List, Set

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

class Interpreter:
    __ast: Statements

    def __init__(self, ast: Statements):
        self.__ast = ast
    
    def get_literal_value(self, literal: Literal) -> any:
        if literal.ltype == LiteralType.NUMBER:
            return int(literal.value)
        elif literal.ltype == LiteralType.STRING:
            return str(literal.value)

    def run(self, ast: Statements = None, scope: Scope = None) -> List[any]:
        if ast == None: ast = self.__ast
        if scope == None: scope = Scope()

        if type(ast) == Statements:
            outputs = []

            for statement in ast:
                output = self.run(statement, scope)

                outputs.append(output)

            return outputs
        elif type(ast) == Assignment:
            value = self.run(ast.statements, scope)[-1]

            scope.put(ast.identifier.value, value)

            return value
        elif type(ast) == Operation:
            value = None
            op = None
            
            for token in ast:
                token_value = None

                if type(token) == Literal:
                    token_value = self.get_literal_value(token)
                elif type(token) == Reserved:
                    op = token.rtype
                elif type(token) == Identifier:
                    try:
                        token_value = scope.get(token.value)
                    except KeyError as err:
                        raise InterpreterError(token.span, "Variable not found in scope.")

                if token_value == None: continue

                if value == None:
                    value = token_value
                    continue

                if op == ReservedType.PLUS:
                    value += token_value
                elif op == ReservedType.MINUS:
                    value -= token_value
                else:
                    raise InterpreterError(token.span, "Unable to handle operation.")     
            
            return value
        elif type(ast) == Show:
            value = self.run(ast.statements, scope)[-1]

            print(value)

            return value

def parse(source: str):
    try:
        return statementize(tokenize(spanize(source)))
    except ParseError as err:
        handle_error(err, source)

def interpret(source: str, ast: Statements):
    try:
        interpeter = Interpreter(ast)
        return interpeter.run()[-1]
    except InterpreterError as err:
        handle_error(err, source)
