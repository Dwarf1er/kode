from .tokens import spanize, tokenize
from .statements import statementize
from .interpreter import interpret
from .errors import ParseError

def parse(source: str):
    try:
        return statementize(tokenize(spanize(source)))
    except ParseError as err:
        spans = err.span

        if not type(spans) == list:
            spans = [spans]

        source_pointers = [False] * len(source)

        for span in spans:
            for i in range(span.offset, span.end):
                source_pointers[i] = True

        print("|")
        print("| PARSE ERROR:", err)
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
