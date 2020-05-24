""" Command line interface using prompt_toolkit. """

import logging
from asyncio import get_event_loop
from prompt_toolkit import __version__ as ptk_version

# Check version of prompt toolkit:
if not ptk_version.startswith("3."):
    print(
        "We require prompt toolkit version 3.x, we currently have: {}".format(
            ptk_version
        )
    )

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.margins import NumberedMargin, ScrollbarMargin
from prompt_toolkit.layout.margins import Margin
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.widgets import Frame

from pygments.lexers import CLexer
from pygments.styles import get_style_by_name

from ... import __version__ as ppci_version
from ...common import logformat


class CurrentAddressMargin(Margin):
    def __init__(self):
        self.current_line = None

    def get_width(self, get_ui_content):
        return 3

    def create_margin(self, window_render_info, width, height):
        result = []
        for lineno in window_render_info.displayed_lines:
            if lineno + 1 == self.current_line:
                result.append(("class:text", ">>\n"))
            else:
                result.append(("class:text", "\n"))
        return result


class MyHandler(logging.Handler):
    """ Handle log messages by putting them into a buffer """

    def __init__(self, buf):
        super().__init__()
        self._buf = buf

    def emit(self, record):
        txt = self.format(record)
        self._buf.text = txt + "\n" + self._buf.text


class DisplayVariablesProcessor(Processor):
    """ Display values of local variables inline """

    def __init__(self):
        self.variables = {}

    def apply_transformation(self, transformation_input):
        tokens = list(transformation_input.fragments)
        row = transformation_input.lineno + 1
        if row in self.variables:
            tokens.append(
                ("class:title", "  // {}".format(self.variables[row]))
            )
        return Transformation(tokens)


class PtDebugCli:
    """ Command line interface using prompt_toolkit. """

    def __init__(self, debugger):
        self._filename = None
        self.sources = {}
        self.debugger = debugger
        self.debugger.events.on_stop += self.on_stop
        self.current_address_margin = CurrentAddressMargin()
        kb = KeyBindings()
        self.locals_processor = DisplayVariablesProcessor()

        self.source_buffer = Buffer(multiline=True)
        self.bar_buffer = Buffer(multiline=True)
        self.register_buffer = Buffer(multiline=True)
        self.logs_buffer = Buffer(multiline=True)

        @kb.add(Keys.F10, eager=True)
        def quit_(event):
            event.app.exit()

        @kb.add(Keys.F8)
        def clear_breakpoint_(event):
            if self.has_source():
                filename, row = self.get_current_location()
                self.debugger.clear_breakpoint(filename, row)

        @kb.add(Keys.F7)
        def set_breakpoint_(event):
            if self.has_source():
                filename, row = self.get_current_location()
                self.debugger.set_breakpoint(filename, row)

        @kb.add(Keys.F6)
        def step_(event):
            self.debugger.step()

        @kb.add(Keys.F5)
        def run_(event):
            self.debugger.run()

        @kb.add(Keys.F4)
        def stop_(event):
            self.debugger.stop()

        @kb.add(Keys.PageUp)
        def scroll_up_(event):
            self.source_buffer.cursor_up(count=15)

        @kb.add(Keys.PageDown)
        def scroll_down_(event):
            self.source_buffer.cursor_down(count=15)

        src_lexer = PygmentsLexer(CLexer)

        source_code_window = Window(
            content=BufferControl(
                buffer=self.source_buffer,
                lexer=src_lexer,
                input_processors=[self.locals_processor],
            ),
            left_margins=[self.current_address_margin, NumberedMargin()],
            right_margins=[ScrollbarMargin(display_arrows=True)],
            cursorline=True,
        )

        register_window = Window(
            content=BufferControl(buffer=self.register_buffer), width=20
        )

        title_text = "Welcome to the ppci debugger version {} running in prompt_toolkit {}".format(
            ppci_version, ptk_version
        )

        help_text = (
            "F4=stop F5=run F6=step F7=set breakpoint"
            + " F8=clear breakpoint F10=exit"
        )

        # Application layout:
        body = HSplit(
            [
                Window(
                    content=FormattedTextControl(text=title_text), height=1
                ),
                VSplit(
                    [
                        HSplit(
                            [
                                Frame(
                                    body=source_code_window,
                                    title="source-code",
                                ),
                                Window(
                                    content=BufferControl(
                                        buffer=self.logs_buffer
                                    ),
                                    height=2,
                                ),
                            ]
                        ),
                        Frame(body=register_window, title="registers"),
                    ]
                ),
                Window(
                    content=FormattedTextControl(self.get_status_tokens),
                    height=1,
                ),
                Window(content=FormattedTextControl(help_text), height=1),
            ]
        )
        layout = Layout(body)

        style = style_from_pygments_cls(get_style_by_name("vim"))

        log_handler = MyHandler(self.logs_buffer)
        fmt = logging.Formatter(fmt=logformat)
        log_handler.setFormatter(fmt)
        log_handler.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(log_handler)

        self._event_loop = get_event_loop()

        self.application = Application(
            layout=layout, style=style, key_bindings=kb, full_screen=True
        )

    def cmdloop(self):
        self.application.run()

    def get_status_tokens(self):
        tokens = []
        tokens.append(
            ("class:status", "STATUS={} ".format(self.debugger.status))
        )
        tokens.append(
            ("class:status", "PC={:08X} ".format(self.debugger.get_pc()))
        )
        if self.debugger.has_symbols:
            loc = self.debugger.find_pc()
            if loc:
                filename, row = loc
                tokens.append(
                    ("class:status", "LOCATION={}:{}".format(filename, row))
                )
        return tokens

    def on_stop(self):
        """ Handle stopped event. """

        def callback():
            self.display_registers()
            self.highlight_source()
            self.evaluate_locals()
            self.application.invalidate()

        self._event_loop.call_soon_threadsafe(callback)

    def evaluate_locals(self):
        # Locals:
        localz = self.debugger.local_vars()
        self.locals_processor.variables.clear()
        for name, var in localz.items():
            value = self.debugger.eval_variable(var)
            var_text = "{} = {}".format(name, value)
            self.locals_processor.variables[var.loc.row] = var_text

    def has_source(self):
        return self._filename is not None

    def get_current_location(self):
        assert self.has_source()
        row = self.source_buffer.document.cursor_position_row + 1
        return self._filename, row

    def highlight_source(self):
        if self.debugger.has_symbols:
            loc = self.debugger.find_pc()
            if loc:
                filename, row = loc
                self.source_buffer.text = self.get_file_source(filename)
                self._filename = filename
                self.source_buffer.cursor_position = 3
                self.current_address_margin.current_line = row
            else:
                self.current_address_margin.current_line = None

    def display_registers(self):
        """ Update register buffer """
        registers = self.debugger.get_registers()
        register_values = self.debugger.get_register_values(registers)
        lines = ["Register values:"]
        if register_values:
            for register, value in register_values.items():
                size = register.bitsize // 4
                lines.append(
                    "{:>5.5s} : 0x{:0{sz}X}".format(
                        str(register), value, sz=size
                    )
                )
        self.register_buffer.text = "\n".join(lines)

    def get_file_source(self, filename):
        if filename not in self.sources:
            with open(filename, "r") as f:
                source = f.read()
            self.sources[filename] = source
        return self.sources[filename]
