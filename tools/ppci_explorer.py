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
import os
from itertools import cycle
import traceback

from pygments.styles import get_style_by_name
from pygments.lexers import CLexer

from prompt_toolkit import Application
import prompt_toolkit as pt
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next
from prompt_toolkit.key_binding.bindings.focus import focus_previous
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout import ScrollbarMargin, NumberedMargin
from prompt_toolkit.widgets import Frame
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.filters import Condition
from prompt_toolkit.styles import style_from_pygments_cls

from ppci import __version__ as ppci_version
from ppci import api
from ppci.binutils.outstream import TextOutputStream
from ppci.common import CompilerError, logformat
from ppci.irutils import print_module
from ppci.lang.c import create_ast, print_ast


class MyHandler(logging.Handler):
    def __init__(self, buf):
        super().__init__()
        self._buf = buf

    def emit(self, record):
        txt = self.format(record)
        self._buf.text = txt + "\n" + self._buf.text


class DisplayErrorsProcessor(Processor):
    def __init__(self):
        self.errors = {}

    def apply_transformation(self, transformation_input):
        tokens = list(transformation_input.fragments)
        lineno = transformation_input.lineno + 1
        if lineno in self.errors:
            tokens.append(("", "// {}".format(self.errors[lineno])))
        return Transformation(tokens)


class PpciExplorer:
    """ Ppci explorer. """

    cache_filename = "ppci_explorer_source.txt"

    def __init__(self):
        available_archs = [
            "arm",
            "x86_64",
            "riscv",
            "avr",
            "or1k",
            "xtensa",
            "microblaze",
            "msp430",
        ]
        # State variables:
        self.arch = available_archs[-1]
        self.stage = "asm"
        self.show_log = False
        self.optimize = False

        self.archs = cycle(available_archs)
        self.stages = cycle(["ir", "ast", "asm"])

        # Some key bindings:
        kb = KeyBindings()

        @kb.add(Keys.F10, eager=True)
        def quit_(event):
            with open(self.cache_filename, "w") as f:
                f.write(self.source_buffer.text)
            event.app.exit()

        kb.add(Keys.F6, eager=True)(self.cycle_stage)
        kb.add(Keys.F7, eager=True)(self.next_architecture)
        kb.add(Keys.F8, eager=True)(self.toggle_optimize)
        kb.add(Keys.F9, eager=True)(self.toggle_log)
        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        log_buffer = Buffer(multiline=True)

        show_log = Condition(lambda: self.show_log)
        self.errors_processor = DisplayErrorsProcessor()

        # Source:
        self.source_buffer = Buffer(multiline=True)
        src_lexer = PygmentsLexer(CLexer)
        code_edit = Window(
            content=BufferControl(
                buffer=self.source_buffer,
                lexer=src_lexer,
                input_processors=[self.errors_processor],
            ),
            left_margins=[NumberedMargin()],
            right_margins=[ScrollbarMargin(display_arrows=True)],
        )

        # Output:
        self.output_buffer = Buffer(multiline=True)
        result_window = Window(
            content=BufferControl(self.output_buffer),
            right_margins=[ScrollbarMargin(display_arrows=True)],
        )
        layout = Layout(
            HSplit(
                [
                    Window(
                        FormattedTextControl(self.get_title_bar_tokens),
                        height=1,
                    ),
                    VSplit(
                        [
                            Frame(body=code_edit, title="source code"),
                            Frame(body=result_window, title="assembly output"),
                            ConditionalContainer(
                                Window(content=BufferControl(log_buffer)),
                                filter=show_log,
                            ),
                        ]
                    ),
                    Window(
                        FormattedTextControl(text="F9=toggle log F10=exit"),
                        height=1,
                        style="class:status",
                    ),
                ]
            )
        )

        style = style_from_pygments_cls(get_style_by_name("vim"))
        log_handler = MyHandler(log_buffer)
        fmt = logging.Formatter(fmt=logformat)
        log_handler.setFormatter(fmt)
        log_handler.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().addHandler(log_handler)

        self.source_buffer.on_text_changed += self.on_change

        self.application = Application(
            layout=layout, key_bindings=kb, style=style, full_screen=True
        )

        if os.path.exists(self.cache_filename):
            with open(self.cache_filename, "r") as f:
                src = f.read()
        else:
            src = DEMO_SOURCE
        self.source_buffer.text = src

    def on_change(self, source_buffer):
        self.do_compile()

    def get_title_bar_tokens(self):
        return (
            "Welcome to the ppci explorer {}".format(ppci_version)
            + "(prompt_toolkit {})".format(pt.__version__)
            + " [Stage = {} (F6)] ".format(self.stage)
            + " [Arch = {} (F7)] ".format(self.arch)
            + " [Optimize = {} (F8)] ".format(self.optimize)
        )

    def do_compile(self):
        """ Try a compilation. """
        self.errors_processor.errors.clear()
        try:
            self.output_buffer.text = self.compile(self.source_buffer.text)
        except CompilerError as ex:
            if ex.loc:
                self.errors_processor.errors[ex.loc.row] = ex.msg
                self.output_buffer.text = "Compiler error: {}".format(ex)
            else:
                self.output_buffer.text = "Compiler error: {}".format(ex)
        except Exception as ex:  # Catch the more hard-core exceptions.
            stderr = io.StringIO()
            print("Other error: {} -> {}".format(type(ex), ex), file=stderr)
            traceback.print_exc(file=stderr)
            self.output_buffer.text = stderr.getvalue()

    def compile(self, source):
        """ Compile the given source with current settings. """
        srcfile = io.StringIO(source)
        outfile = io.StringIO()
        if self.stage == "ast":
            src_ast = create_ast(srcfile, api.get_arch(self.arch).info)
            print_ast(src_ast, file=outfile)
        else:
            ir_module = api.c_to_ir(srcfile, self.arch)

            if self.optimize:
                api.optimize(ir_module, level=2)

            if self.stage == "ir":
                print_module(ir_module, file=outfile)
            else:
                text_stream = TextOutputStream(f=outfile, add_binary=True)
                api.ir_to_stream(ir_module, self.arch, text_stream)
        return outfile.getvalue()

    def cycle_stage(self, _):
        """ Cycle between AST, ir or assembly. """
        self.stage = next(self.stages)
        self.do_compile()

    def next_architecture(self, _):
        """ Cycle into the next architecture. """
        self.arch = next(self.archs)
        self.do_compile()

    def toggle_optimize(self, _):
        """ Toggle optimization. """
        self.optimize = not self.optimize
        self.do_compile()

    def toggle_log(self, _):
        """ Toggle logging. """
        self.show_log = not self.show_log


def ppci_explorer():
    """ Run the ppci explorer. """
    explorer = PpciExplorer()
    explorer.application.run()


DEMO_SOURCE = """
int add(int a, int b) {
    return a + b;
}
"""


if __name__ == "__main__":
    ppci_explorer()
