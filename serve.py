from kode import statementize, tokenize, spanize, Interpreter
from kode.errors import handle_error
from flask import Flask, render_template, request
import os.path

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/examples")
def examples():
    return render_template("examples.html")

@app.route("/kode")
def kode():
    code=""
    if "example" in request.args:
        path=f'./examples/{request.args["example"]}.kode'
        if os.path.exists(path):
            with open(path) as h:
                code=h.read()
    return render_template("kode.html", code=code)

@app.route("/kode", methods=["POST"])
def kode_post():
    try:
        error = False
        spans = spanize(request.form["code"], "web")
        tokens = tokenize(spans)
        ast = statementize(tokens)
        interpreter = Interpreter(ast, silent=True)
        interpreter.run()
        output = interpreter.stdout
    except Exception as err:
        error = True
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
    return render_template("kode.html", code=request.form["code"], output=output, error=error)

app.run(host="0.0.0.0", port=1234, debug=True)