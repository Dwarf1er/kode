from .span import Span

def print_span(span: Span):
    file_path = span.file_path 
    with open(file_path) as h:
        source = h.read()

    source_pointers = [False] * len(source)

    for i in range(span.start, span.end):
        source_pointers[i] = True

    start = 0
    source_split = source.split("\n")

    for i, line in enumerate(source_split, 1):
        end = start + len(line) + 1
        ptrs = source_pointers[start:end]

        if any(ptrs):
            line_num = f"({file_path}:{i}:{ptrs.index(True) + 1})"
            print(f"| {line_num}", line.replace("\t", " "))
            print("|" + " " * (len(line_num) + 1), ''.join("^" if p else " " for p in ptrs))

        start = end
