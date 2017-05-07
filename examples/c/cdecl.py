""" Implement alike logic as is done on www.cdecl.org """
import argparse
import io
from ppci.lang.c import CLexer, CParser, nodes, COptions, CContext
from ppci.lang.c.preprocessor import prepare_for_parsing

parser = argparse.ArgumentParser()
parser.add_argument('source', type=str)
args = parser.parse_args()
# print('Source:', args.source)

# Parse into ast:
coptions = COptions()
ccontext = CContext(coptions, None)
cparser = CParser(ccontext)
clexer = CLexer(COptions())
f = io.StringIO(args.source)
tokens = clexer.lex(f, '<snippet>')
tokens = prepare_for_parsing(tokens, cparser.keywords)
cparser.init_lexer(tokens)
decl = cparser.parse_declaration()[0]

# Explain:
def explain(x):
    if isinstance(x, nodes.VariableDeclaration):
        return '{} is {}'.format(x.name, explain(x.typ))
    elif isinstance(x, nodes.PointerType):
        return 'a pointer to {}'.format(explain(x.pointed_type))
    elif isinstance(x, nodes.ArrayType):
        return 'an array of {}'.format(explain(x.element_type))
    elif isinstance(x, nodes.BareType):
        return '{}'.format(x.type_id)
    else:
        print('???', x)

print(explain(decl))
