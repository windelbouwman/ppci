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
import logging

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
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.controls import FillControl, BufferControl
from prompt_toolkit.layout.controls import TokenListControl
from prompt_toolkit.layout.margins import NumberredMargin, ScrollbarMargin
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.filters import Condition

from ppci import __version__ as ppci_version
from ppci import api
from ppci.binutils.outstream import TextOutputStream
from ppci.common import CompilerError, logformat


def get_title_bar_tokens(cli):
    return [
        (Token.Title,
         'Welcome to the ppci explorer version {}'.format(ppci_version)),
        (Token.Title,
         ' [Arch = {} (F7)] '.format(compiler.arch)),
        (Token.Title,
         ' [Optimize = {} (F8)] '.format(compiler.optimize)),
    ]


def get_help_tokens(cli):
    return [
        (Token.Toolbar.Status,
         'F9=toggle log F10=exit ')]


class MyHandler(logging.Handler):
    def __init__(self, buf):
        super().__init__()
        self._buf = buf

    def emit(self, record):
        txt = self.format(record)
        self._buf.text = txt + '\n' + self._buf.text


class DisplayErrorsProcessor(Processor):
    def __init__(self):
        self.errors = {}

    def apply_transformation(self, cli, document, lineno, source_to_display, tokens):
        tokens = list(tokens)
        if lineno + 1 in self.errors:
            tokens.append((Token.Title,
                           '// {}'.format(self.errors[lineno + 1])))
        return Transformation(tokens)


def arch_gen(archs):
    """ Endless sequence of architectures """
    while True:
        for a in archs:
            yield a


class Compiler:
    def __init__(self):
        self.archs = arch_gen([
            'arm', 'x86_64', 'riscv', 'avr', 'or1k', 'xtensa'])
        self.next_architecture()
        self.show_log = False
        self.optimize = False

    def compile(self, source):
        f = io.StringIO(source)
        ir_module = api.c_to_ir(f, self.arch)
        f2 = io.StringIO()
        if self.optimize:
            api.optimize(ir_module, level=2)
        text_stream = TextOutputStream(f=f2)
        api.ir_to_stream(ir_module, self.arch, text_stream)
        return f2.getvalue()

    def next_architecture(self):
        self.arch = next(self.archs)

    def toggle_log(self):
        self.show_log = not self.show_log

    def toggle_optimize(self):
        self.optimize = not self.optimize


compiler = Compiler()


def ppci_explorer():
    key_binding_manager = KeyBindingManager()
    registry = key_binding_manager.registry

    @registry.add_binding(Keys.F10, eager=True)
    def quit_(event):
        event.cli.set_return_value(None)

    @registry.add_binding(Keys.F7, eager=True)
    def next_arch_(event):
        compiler.next_architecture()
        do_compile()

    @registry.add_binding(Keys.F9, eager=True)
    def toggle_log_(event):
        compiler.toggle_log()

    @registry.add_binding(Keys.F8, eager=True)
    def toggle_optimize_(event):
        compiler.toggle_optimize()
        do_compile()

    show_log = Condition(lambda cli: compiler.show_log)
    src_lexer = PygmentsLexer(CLexer)
    errors_processor = DisplayErrorsProcessor()
    layout = HSplit([
        Window(content=TokenListControl(get_title_bar_tokens, align_center=True), height=D.exact(1)),
        Window(content=FillControl('='), height=D.exact(1)),
        VSplit([
            Window(content=FillControl('|'), width=D.exact(1)),
            Window(content=BufferControl(
                'source', lexer=src_lexer, input_processors=[errors_processor]), left_margins=[NumberredMargin()], right_margins=[ScrollbarMargin()], cursorline=True),
            Window(content=FillControl('|'), width=D.exact(1)),
            Window(content=BufferControl('output')),
            Window(content=FillControl(
                '|', token=Token.Line), width=D.exact(1)),
            ConditionalContainer(
                Window(content=BufferControl('logs')),
                filter=show_log),
        ]),
        Window(content=FillControl('='), height=D.exact(1)),
        Window(content=TokenListControl(get_help_tokens), height=D.exact(1)),
    ])

    style = style_from_pygments(get_style_by_name('vim'))
    buffers = {
        'source': Buffer(is_multiline=True),
        'output': Buffer(is_multiline=True),
        'logs': Buffer(is_multiline=True),
    }

    log_handler = MyHandler(buffers['logs'])
    fmt = logging.Formatter(fmt=logformat)
    log_handler.setFormatter(fmt)
    log_handler.setLevel(logging.DEBUG)
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(log_handler)

    def on_change(source_buffer):
        do_compile()

    def do_compile():
        errors_processor.errors.clear()
        try:
            buffers['output'].text = compiler.compile(buffers['source'].text)
        except CompilerError as ex:
            if ex.loc:
                errors_processor.errors[ex.loc.row] = ex.msg
                buffers['output'].text = ''
            else:
                buffers['output'].text = str(ex)

    buffers['source'].on_text_changed += on_change

    application = Application(
        layout=layout, buffers=buffers, style=style,
        key_bindings_registry=registry, use_alternate_screen=True,
        )

    buffers['source'].text = """
    int g;

    int add(int a, int b) {
      return a + b - g;
    }
    """

    loop = create_eventloop()
    cli = CommandLineInterface(application=application, eventloop=loop)
    cli.focus('source')
    cli.run()


if __name__ == '__main__':
    ppci_explorer()
