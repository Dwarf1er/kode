from .utils import Span

class ParseError(Exception):
    span: Span

    def __init__(self, span: Span, message: str):
        self.span = span
        super().__init__(message)