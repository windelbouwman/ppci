""" Compile code from the browser and run it in the browser.

Idea from the compiler explorer project:

https://godbolt.org/

Idea:

- Take snippet of C-code
- Compile it using ppci
- Run it as web assembly in the browser again

"""

# Idea: maybe this could be a ipython plugin?

import io

from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.application import Application
from pygments.styles import get_style_by_name
from prompt_toolkit.styles.from_pygments import style_from_pygments
from pygments.token import Token
from prompt_toolkit.key_binding.manager import KeyBindingManager
from pygments.lexers import CLexer
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.controls import FillControl, BufferControl
from prompt_toolkit.layout.controls import TokenListControl
from prompt_toolkit.layout.margins import NumberredMargin, ScrollbarMargin

from ppci import __version__ as ppci_version
from ppci import api
from ppci.binutils.outstream import TextOutputStream
from ppci.common import CompilerError


def get_title_bar_tokens(cli):
    return [
        (Token.Title, 'Welcome to the ppci explorer version {}'.format(ppci_version)),
    ]


def get_help_tokens(cli):
    return [
        (Token.Toolbar.Status, 'F10=exit '),
    ]


def ppci_explorer():
    key_binding_manager = KeyBindingManager()
    registry = key_binding_manager.registry

    @registry.add_binding(Keys.F10, eager=True)
    def quit_(event):
        event.cli.set_return_value(None)

    src_lexer = PygmentsLexer(CLexer)
    layout = HSplit([
        Window(content=TokenListControl(get_title_bar_tokens, align_center=True), height=D.exact(1)),
        Window(content=FillControl('='), height=D.exact(1)),
        VSplit([
            Window(content=FillControl('|'), width=D.exact(1)),
            Window(content=BufferControl('source', lexer=src_lexer), left_margins=[NumberredMargin()], right_margins=[ScrollbarMargin()], cursorline=True),
            Window(content=FillControl('|'), width=D.exact(1)),
            Window(content=BufferControl('output')),
            Window(content=FillControl('|', token=Token.Line), width=D.exact(1)),
        ]),
        Window(content=FillControl('='), height=D.exact(1)),
        Window(content=TokenListControl(get_help_tokens), height=D.exact(1)),
    ])

    style = style_from_pygments(get_style_by_name('vim'))
    buffers = {
        'source': Buffer(is_multiline=True),
        'output': Buffer(is_multiline=True),
    }
    buffers['source'].text = """
    int add(int a, int b) {
      return a + b;
    }
    """

    def on_change(source_buffer):
        try:
            f = io.StringIO(source_buffer.text)
            arch = 'arm'
            ir_module = api.c_to_ir(f, arch)
            f2 = io.StringIO()
            text_stream = TextOutputStream(f=f2)
            api.ir_to_stream(ir_module, arch, text_stream)
            buffers['output'].text = f2.getvalue()
        except CompilerError:
            pass

    buffers['source'].on_text_changed += on_change

    application = Application(
        layout=layout, buffers=buffers, style=style,
        key_bindings_registry=registry, use_alternate_screen=True,
        )

    loop = create_eventloop()
    cli = CommandLineInterface(application=application, eventloop=loop)
    cli.focus('source')
    cli.run()


if __name__ == '__main__':
    ppci_explorer()
