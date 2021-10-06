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

def handle_error(error: KodeError, source: str):
    spans = error.span

    if not type(spans) == list:
        spans = [spans]

    source_pointers = [False] * len(source)

    for span in spans:
        for i in range(span.offset, span.end):
            source_pointers[i] = True

    print(f"|\n| {error.__class__.__name__}:", error, "\n|")

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

    exit(1)
