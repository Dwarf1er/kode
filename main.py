import argparse
from kode import parse, interpret

def main():
    parser = argparse.ArgumentParser(description="Parser for Kode")
    parser.add_argument("--ast", action='store_true', help="Prints the AST representation of the code.")
    parser.add_argument("file", help="File to interpret.")
    args = parser.parse_args()

    file_path = args.file
    with open(args.file) as h:
        source = h.read()

    AST = parse(source, file_path)

    if AST == None: return

    if args.ast: print(AST)

    result = interpret(AST)

    if result == None: return

if __name__ == "__main__":
    main()
