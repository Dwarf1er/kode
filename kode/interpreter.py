from .statements import Statements, Assignment, Operation, Tee
from .tokens import Literal, LiteralType, ReservedType, Reserved, Identifier
from .errors import InterpreterError
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
            scope.push()

            value = self.run(ast.statements, scope)[-1]

            scope.pop()

            scope.put(ast.identifier.value, value)

            return value
        elif type(ast) == Operation:
            value = None
            op = None
            
            for token in ast:
                v = None

                if type(token) == Literal:
                    v = self.get_literal_value(token)
                elif type(token) == Reserved:
                    op = token.rtype
                elif type(token) == Identifier:
                    try:
                        v = scope.get(token.value)
                    except KeyError as err:
                        raise InterpreterError(token.span, "Variable not found in scope.")

                if v == None: continue

                if value == None:
                    value = v
                    continue

                if op == ReservedType.PLUS:
                    value += v
                elif op == ReservedType.MINUS:
                    value -= v
                else:
                    raise InterpreterError(token.span, "Unable to handle operation.")     
            
            return value
        elif type(ast) == Tee:
            value = self.run(ast.statements, scope)[-1]

            print(value)

            return value

def interpret(source: str, ast: Statements):
    interpeter = Interpreter(ast)

    try:
        return interpeter.run()[-1]
    except InterpreterError as err:
        spans = err.span

        if not type(spans) == list:
            spans = [spans]

        source_pointers = [False] * len(source)

        for span in spans:
            for i in range(span.offset, span.end):
                source_pointers[i] = True

        print("|")
        print("| INTERPRETER ERROR:", err)
        print("|")

        start = 0
        source_split = source.split("\n")
        for i, line in enumerate(source_split, 1):
            end = start + len(line) + 1
            ptrs = source_pointers[start:end]

            if any(ptrs):
                line_num = ("(%0"+ str((len(source_split) // 10) + 1) +"d)") % i
                print(f"| {line_num}", line.replace("\t", " "))
                print("|" + " " * (len(line_num) + 1), ''.join("^" if p else " " for p in ptrs))

            start = end
