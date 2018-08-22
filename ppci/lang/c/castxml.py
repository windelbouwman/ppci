import xml.etree.ElementTree as ET
from .nodes import nodes


class CastXmlReader:
    """ Reads xml produced by cast xml for further processing.

    Cast xml converts (compiles) C code to xml format.

    https://github.com/CastXML/CastXML
    """
    def process(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        for child in root:
            print(child)

        declarations = []
        cu = nodes.CompilationUnit(declarations)
        return cu
