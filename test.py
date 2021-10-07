import argparse
from kode import statementize, tokenize, spanize, Interpreter
import glob
import os.path
import time

def main():
    parser = argparse.ArgumentParser(description="UnitTest Kode")
    parser.add_argument("--new", "-n", action='store_true', help="Added or resets unit test values.")
    args = parser.parse_args()

    test_files = glob.glob("./tests/*.kode")
    test_success = 0
    test_count = len(test_files)
    test_fails = []
    
    start_time = time.time_ns()

    for path in test_files:
        with open(path) as h:
            source = h.read()

        result = None
        result_path = os.path.splitext(path)[0] + ".out"
        try:
            with open(result_path) as h:
                result = h.read()
        except Exception as err:
            pass

        try:
            spans = spanize(source, path)
            tokens = tokenize(spans)
            ast = statementize(tokens)
            interpreter = Interpreter(ast, silent=True)
            interpreter.run()

            if args.new:
                result = interpreter.stdout
                with open(result_path, "w") as h:
                    h.write(result)

            if not interpreter.stdout == result: raise Exception(f"Test failed.")
            
            test_success += 1
            print(f"[+] {path} ({test_success}/{test_count})")
        except Exception as err:
            test_fails.append(path)
            print(f"[-] {path} ({test_success}/{test_count}) -> {err}")
    
    end_time = time.time_ns()

    print()
    print(f"Time: {end_time - start_time}ns")
    print(f"Success: {test_success}/{test_count} ({test_success / test_count * 100}%)")

    if len(test_fails) > 0:
        print(f"Fail: {', '.join(test_fails)}")

if __name__ == "__main__":
    main()
