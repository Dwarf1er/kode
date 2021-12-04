from kode import statementize, tokenize, spanize, Interpreter
from kode.errors import handle_error, KodeError
from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/examples")
def examples():
    root_dir = "./examples"
    examples = []
    for sub_dir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".kode"):
                examples.append(file.split(".kode")[0])
    return render_template("examples.html", examples=examples)

@app.route("/playground")
def kode():
    code=""
    if "example" in request.args:
        path=f'./examples/{request.args["example"]}.kode'
        if os.path.exists(path):
            with open(path) as h:
                code=h.read()
    return render_template("playground.html", code=code)

@app.route("/playground", methods=["POST"])
def kode_post():
    interpreter = None
    try:
        user_input = request.form["input"].split("\n")

        def get_input() -> str:
            if len(user_input) == 0:
                return None
            return user_input.pop(0).strip()

        error = False
        spans = spanize(request.form["code"], "web")
        tokens = tokenize(spans)
        ast = statementize(tokens)
        interpreter = Interpreter(ast, silent=True, input_method=get_input)
        interpreter.run()
        output = interpreter.stdout
    except Exception as err:
        if not isinstance(err, KodeError):
            raise err

        error = True
        if interpreter:
            output = interpreter.stdout
        else:
            output = ""
        output += f"|\n| {err.__class__.__name__}: " + str(err) + "\n|\n"
        span = err.span
        source = request.form['code']
        source_pointers = [False] * len(source)

        for i in range(span.start, span.end):
            source_pointers[i] = True

        start = 0
        source_split = source.split("\n")

        for i, line in enumerate(source_split, 1):
            end = start + len(line) + 1
            ptrs = source_pointers[start:end]

            if any(ptrs):
                line_num = f"(web:{i}:{ptrs.index(True) + 1})"
                output += f"| {line_num} " + line.replace("\t", " ") + "\n"
                output += "|" + " " * (len(line_num) + 1) + " " + ''.join("^" if p else " " for p in ptrs) + "\n"

            start = end
    return render_template("playground.html", code=request.form["code"], input=request.form["input"], output=output, error=error)

if __name__ == "__main__":
    app.run(port=5000)