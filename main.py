import argparse
from kode import parse

def main():
    parser = argparse.ArgumentParser(description="Parser for Kode")
    parser.add_argument("--ast", action='store_true', help="Prints the AST representation of the code.")
    parser.add_argument("file", help="File to interpret.")
    args = parser.parse_args()

    with open(args.file) as h:
        source = h.read()

    AST = parse(source)

    if not AST: return

    if args.ast: print(AST)

if __name__ == "__main__":
    main()
