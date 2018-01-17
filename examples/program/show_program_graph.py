""" Show graph structure of how programs can be compiled into one another,
using HTML.
"""

import os
import tempfile
import webbrowser

from ppci.programs import get_program_classes_html


total_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PPCI program class graph</title>
</head>
<body>
{}
</body>
</html>
""".format(get_program_classes_html())

filename = os.path.join(tempfile.gettempdir(), 'ppci_program_graph.html')
with open(filename, 'wb') as f:
    f.write(total_html.encode())

webbrowser.open(filename)
