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

from prompt_toolkit import Application
import prompt_toolkit as pt
from pygments.styles import get_style_by_name
from prompt_toolkit.styles import style_from_pygments_cls
from pygments.token import Token
from prompt_toolkit.key_binding import KeyBindings
from pygments.lexers import CLexer
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout import ScrollbarMargin, NumberedMargin
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.filters import Condition

from ppci import __version__ as ppci_version
from ppci import api
from ppci.binutils.outstream import TextOutputStream
from ppci.common import CompilerError, logformat


def get_title_bar_tokens():
    return \
         'Welcome to the ppci explorer version {} (prompt_toolkit {})'.format(ppci_version, pt.__version__) + \
         ' [Arch = {} (F7)] '.format(compiler.arch) + \
         ' [Optimize = {} (F8)] '.format(compiler.optimize)


def get_help_tokens():
    return 'F9=toggle log F10=exit '


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


class CodeEdit:
    def __init__(self):
        self.buffer = Buffer()
        src_lexer = PygmentsLexer(CLexer)
        self.control = BufferControl(
            buffer=self.buffer,
            lexer=src_lexer,
        )
        self.window = Window(
            content=self.control,
            left_margins=[NumberedMargin()],
            right_margins=[ScrollbarMargin(display_arrows=True)],
        )

    def __pt_container__(self):
        return self.window


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
    kb = KeyBindings()

    @kb.add(Keys.F10, eager=True)
    def quit_(event):
        event.app.exit()

    @kb.add(Keys.F7, eager=True)
    def next_arch_(event):
        compiler.next_architecture()
        do_compile()

    @kb.add(Keys.F9, eager=True)
    def toggle_log_(event):
        compiler.toggle_log()

    @kb.add(Keys.F8, eager=True)
    def toggle_optimize_(event):
        compiler.toggle_optimize()
        do_compile()

    buffers = {
        'output': Buffer(multiline=True),
        'logs': Buffer(multiline=True),
    }

    show_log = Condition(lambda: compiler.show_log)
    errors_processor = DisplayErrorsProcessor()
    code_edit = CodeEdit()
    source_buffer = code_edit.buffer
    layout = Layout(HSplit([
        Window(FormattedTextControl(get_title_bar_tokens), height=1),
        VSplit([
            Frame(
                body=code_edit, title="source code",
            ),
            Frame(
                body=Window(content=BufferControl(buffers['output'])),
                title='assembly output'
            ),
            ConditionalContainer(
                Window(content=BufferControl(buffers['logs'])),
                filter=show_log),
        ]),
        Window(FormattedTextControl(get_help_tokens), height=1),
    ]))

    style = style_from_pygments_cls(get_style_by_name('vim'))
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
            buffers['output'].text = compiler.compile(source_buffer.text)
        except CompilerError as ex:
            if ex.loc:
                errors_processor.errors[ex.loc.row] = ex.msg
                buffers['output'].text = ''
            else:
                buffers['output'].text = str(ex)

    source_buffer.on_text_changed += on_change

    application = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True)

    source_buffer.text = """
    int g=23;

    int add(int a, int b) {
      return a + b - g;
    }
    """

    application.run()


if __name__ == '__main__':
    ppci_explorer()
