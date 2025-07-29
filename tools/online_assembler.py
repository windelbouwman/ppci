"""Helper to assemble code from a web page."""

import flask
import subprocess
import tempfile

main_html = r"""
<!DOCTYPE html>
<html><head>
<title>Online compiler</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="http://www.w3schools.com/lib/w3.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
<script>
function do_compile() {
 source = $("#source").val()
 $.post("compile", { source: source },
  function(data, status) {
   $("#result").text(data.replace("\\n", "<br>", "g"));
  });
}
</script>
</head>
<body>
<div class="w3-container w3-teal"><h1>Online assembler</h1></div>
<div class="w3-container"><textarea id="source">mov rax,rbx</textarea></div>
<div class="w3-container">
<button class="w3-btn" onclick="do_compile()">Compile</button>
</div>
<div class="w3-container"><p id="result"></p></div>
<div class="w3-container w3-teal"><p>By Windel Bouwman 2016</p></div>
</body></html>
"""

app = flask.Flask(__name__)


@app.route("/")
def main():
    return main_html


@app.route("/compile", methods=["POST"])
def compile():
    source = flask.request.form["source"]
    _, tmp = tempfile.mkstemp()
    print(tmp)
    with open(tmp, "w") as f:
        f.write(source)
    # res2 = asm_x86(tmp)
    res2 = asm_arm(tmp)
    return str(source) + str(res2.stdout)


def asm_x86(tmp):
    res = subprocess.run(["nasm", "-f", "elf64", tmp])
    print(res)
    res2 = subprocess.run(
        ["objdump", "-d", tmp + ".o"], stdout=subprocess.PIPE
    )
    print(res2)
    return res2


def asm_arm(tmp):
    res = subprocess.run(["arm-none-eabi-as", tmp])
    print(res)
    res2 = subprocess.run(
        ["arm-none-eabi-objdump", "-d"], stdout=subprocess.PIPE
    )
    print(res2)
    return res2


if __name__ == "__main__":
    app.run()
