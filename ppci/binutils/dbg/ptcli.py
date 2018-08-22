""" Command line interface using prompt_toolkit. """

import logging

from ... import __version__ as ppci_version
from ...common import logformat

# TODO: switch to prompt toolkit 2.0

# from prompt_toolkit import prompt
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.application import Application
from pygments.styles import get_style_by_name
from prompt_toolkit.styles.from_pygments import style_from_pygments
from pygments.token import Token
from prompt_toolkit.key_binding.manager import KeyBindingManager
from pygments.lexers import PythonLexer, CLexer
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.shortcuts import create_eventloop
# from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.controls import FillControl, BufferControl
from prompt_toolkit.layout.controls import TokenListControl
from prompt_toolkit.layout.margins import NumberredMargin, ScrollbarMargin
from prompt_toolkit.layout.margins import Margin, PromptMargin
from prompt_toolkit.layout.processors import Processor, Transformation
# from prompt_toolkit.layout.layout import Layout


def get_title_bar_tokens(cli):
    return [(
        Token.Title,
        'Welcome to the ppci debugger version {}'.format(ppci_version)
    )]


def get_help_tokens(cli):
    return [(
        Token.Title,
        'F4=stop F5=run F6=step F7=set breakpoint F8=clear breakpoint F10=exit'
    )]


class StatusToolbar(TokenListControl):
    def __init__(self, debugger):
        def get_tokens(cli):
            tokens = []
            tokens.append((Token.Toolbar.Status, 'STATUS={} '.format(debugger.status)))
            tokens.append((Token.Toolbar.Status, 'PC={} '.format(debugger.get_pc())))
            if debugger.has_symbols:
                loc = debugger.find_pc()
                if loc:
                    filename, row = loc
                    tokens.append((Token.Toolbar.Status, 'LOCATION={}:{}'.format(filename, row)))
            return tokens

        super().__init__(get_tokens)


class CurrentAddressMargin(Margin):
    def __init__(self):
        self.current_line = None

    def get_width(self, cli, get_ui_content):
        return 3

    def create_margin(self, cli, window_render_info, width, height):
        result = []
        for lineno in window_render_info.displayed_lines:
            if lineno + 1 == self.current_line:
                result.append((Token, '>>\n'))
            else:
                result.append((Token, '\n'))
        return result


class MyHandler(logging.Handler):
    """ Handle log messages by putting them into a buffer """
    def __init__(self, buf):
        super().__init__()
        self._buf = buf

    def emit(self, record):
        txt = self.format(record)
        self._buf.text = txt + '\n' + self._buf.text


class DisplayVariablesProcessor(Processor):
    """ Display values of local variables inline """
    def __init__(self):
        self.variables = {}

    def apply_transformation(
            self, cli, document, lineno, source_to_display, tokens):
        tokens = list(tokens)
        row = lineno + 1
        if row in self.variables:
            tokens.append((Token.Title,
                           '  // {}'.format(self.variables[row])))
        return Transformation(tokens)


class PtDebugCli:
    """ Command line interface using prompt_toolkit. """

    def __init__(self, debugger):
        self._filename = None
        self.sources = {}
        self.debugger = debugger
        self.debugger.events.on_stop += self.on_stop
        self.current_address_margin = CurrentAddressMargin()
        # kb = KeyBindings()
        self.key_binding_manager = KeyBindingManager()
        registry = self.key_binding_manager.registry
        self.locals_processor = DisplayVariablesProcessor()

        @registry.add_binding(Keys.F10, eager=True)
        def quit_(event):
            event.cli.set_return_value(None)

        @registry.add_binding(Keys.F8)
        def clear_breakpoint_(event):
            if self.has_source():
                filename, row = self.get_current_location()
                self.debugger.clear_breakpoint(filename, row)

        @registry.add_binding(Keys.F7)
        def set_breakpoint_(event):
            if self.has_source():
                filename, row = self.get_current_location()
                self.debugger.set_breakpoint(filename, row)

        @registry.add_binding(Keys.F6)
        def step_(event):
            self.debugger.step()

        @registry.add_binding(Keys.F5)
        def run_(event):
            self.debugger.run()

        @registry.add_binding(Keys.F4)
        def run_(event):
            self.debugger.stop()

        @registry.add_binding(Keys.PageUp)
        def scroll_up_(event):
            source_buffer = self.buffers['source']
            source_buffer.cursor_up(count=15)

        @registry.add_binding(Keys.PageDown)
        def scroll_down_(event):
            source_buffer = self.buffers['source']
            source_buffer.cursor_down(count=15)

        src_lexer = PygmentsLexer(CLexer)
        layout = HSplit([
            Window(content=TokenListControl(get_title_bar_tokens, align_center=True), height=D.exact(1)),
            Window(content=FillControl('='), height=D.exact(1)),
            VSplit([
                Window(content=FillControl('|'), width=D.exact(1)),
                HSplit([
                    Window(content=BufferControl('source', lexer=src_lexer, input_processors=[self.locals_processor]), left_margins=[self.current_address_margin, NumberredMargin()], right_margins=[ScrollbarMargin()], cursorline=True),
                    Window(content=FillControl('='), height=D.exact(1)),
                    Window(content=BufferControl('logs'), height=D.exact(2)),
                ]),
                Window(content=FillControl('|'), width=D.exact(1)),
                Window(content=BufferControl('registers'), width=D.exact(20)),
                Window(content=FillControl('|', token=Token.Line), width=D.exact(1)),
            ]),
            Window(content=FillControl('='), height=D.exact(1)),
            Window(content=BufferControl(buffer_name=DEFAULT_BUFFER), height=D.exact(2)),
            Window(content=StatusToolbar(debugger), height=D.exact(1)),
            Window(content=TokenListControl(get_help_tokens), height=D.exact(1)),
        ])

        style = style_from_pygments(get_style_by_name('vim'))
        self.buffers = {
            'source': Buffer(is_multiline=True),
            'bar': Buffer(is_multiline=True),
            'registers': Buffer(is_multiline=True),
            'logs': Buffer(is_multiline=True),
        }

        log_handler = MyHandler(self.buffers['logs'])
        fmt = logging.Formatter(fmt=logformat)
        log_handler.setFormatter(fmt)
        log_handler.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(log_handler)

        self.application = Application(
            layout=layout,
            buffers=self.buffers,
            style=style,
            key_bindings_registry=registry,
            use_alternate_screen=True,
            )
        self._event_loop = create_eventloop()

    def cmdloop(self):
        self.cli = CommandLineInterface(
            application=self.application, eventloop=self._event_loop)
        self.cli.focus('source')
        self.cli.run()

    def on_stop(self):
        """ Handle stopped event. """
        def callback():
            self.display_registers()
            self.highlight_source()
            self.evaluate_locals()
            self.cli.request_redraw()
        self._event_loop.call_from_executor(callback)

    def evaluate_locals(self):
        # Locals:
        localz = self.debugger.local_vars()
        self.locals_processor.variables.clear()
        for name, var in localz.items():
            value = self.debugger.eval_variable(var)
            var_text = '{} = {}'.format(name, value)
            self.locals_processor.variables[var.loc.row] = var_text

    def has_source(self):
        return self._filename is not None

    def get_current_location(self):
        assert self.has_source()
        source_buffer = self.buffers['source']
        row = source_buffer.document.cursor_position_row + 1
        return self._filename, row

    def highlight_source(self):
        if self.debugger.has_symbols:
            loc = self.debugger.find_pc()
            if loc:
                filename, row = loc
                source_buffer = self.buffers['source']
                source_buffer.text = self.get_file_source(filename)
                self._filename = filename
                source_buffer.cursor_position = 3
                self.current_address_margin.current_line = row
            else:
                self.current_address_margin.current_line = None

    def display_registers(self):
        """ Update register buffer """
        register_buffer = self.buffers['registers']
        registers = self.debugger.get_registers()
        register_values = self.debugger.get_register_values(registers)
        lines = ['Register values:']
        if register_values:
            for register, value in register_values.items():
                size = register.bitsize // 4
                lines.append('{:>5.5s} : 0x{:0{sz}X}'.format(
                    str(register), value, sz=size))
        register_buffer.text = '\n'.join(lines)

    def get_file_source(self, filename):
        if filename not in self.sources:
            with open(filename, 'r') as f:
                source = f.read()
            self.sources[filename] = source
        return self.sources[filename]
