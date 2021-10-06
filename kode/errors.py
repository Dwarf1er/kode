from kode.utils import print_span
from .span import Span

class KodeError(Exception):
    span: Span

    def __init__(self, span: Span, message: str):
        self.span = span
        super().__init__(message)

class ParseError(KodeError):
    def __init__(self, span: Span, message: str):
        super().__init__(span, message)
    
class InterpreterError(KodeError):
    def __init__(self, span: Span, message: str):
        super().__init__(span, message)

def handle_error(error: KodeError):
    print(f"|\n| {error.__class__.__name__}:", error, "\n|")

    print_span(error.span)

    exit(1)
