""" Command line interface using prompt_toolkit. """

from ppci import __version__ as ppci_version
# from prompt_toolkit import prompt
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.application import Application
from pygments.styles import get_style_by_name
from prompt_toolkit.styles.from_pygments import style_from_pygments
from pygments.token import Token
from prompt_toolkit.key_binding.manager import KeyBindingManager
from pygments.lexers import PythonLexer
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
# from prompt_toolkit.layout.layout import Layout


def get_title_bar_tokens(cli):
    return [
        (Token.Title, 'Welcome to the ppci debugger version {}'.format(ppci_version)),
    ]


def get_help_tokens(cli):
    return [
        (Token.Title, 'F5=run F6=step F10=exit'),
    ]


class StatusToolbar(TokenListControl):
    def __init__(self, debugger):
        def get_tokens(cli):
            tokens = []
            tokens.append((Token.Toolbar.Status, 'STATUS={} '.format(debugger.status)))
            tokens.append((Token.Toolbar.Status, 'PC={} '.format(debugger.get_pc())))
            if debugger.has_symbols:
                filename, row = debugger.find_pc()
                tokens.append((Token.Toolbar.Status, 'LOCATION={}:{}'.format(filename, row)))
            return tokens

        super().__init__(get_tokens)


class PtDebugCli:
    """ Command line interface using prompt_toolkit. """

    def __init__(self, debugger):
        self.debugger = debugger
        # kb = KeyBindings()
        self.key_binding_manager = KeyBindingManager()
        registry = self.key_binding_manager.registry

        @registry.add_binding(Keys.F10, eager=True)
        def quit_(event):
            event.cli.set_return_value(None)

        @registry.add_binding(Keys.F6)
        def step_(event):
            self.debugger.step()

        @registry.add_binding(Keys.F5)
        def run_(event):
            self.debugger.run()

        src_lexer = PygmentsLexer(PythonLexer)
        layout = HSplit([
            Window(content=TokenListControl(get_title_bar_tokens, align_center=True), height=D.exact(1)),
            Window(content=FillControl('='), height=D.exact(1)),
            VSplit([
                Window(content=FillControl('|'), width=D.exact(1)),
                Window(content=BufferControl('source', lexer=src_lexer), left_margins=[NumberredMargin()], right_margins=[ScrollbarMargin()], cursorline=True),
                Window(content=FillControl('|'), width=D.exact(1)),
                Window(content=BufferControl('registers'), width=D.exact(30)),
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
        }
        self.buffers['registers'].text = 'r1=00\nr2=200'
        self.buffers['source'].text = open(__file__, 'r').read()

        self.application = Application(
            layout=layout,
            buffers=self.buffers,
            style=style,
            key_bindings_registry=registry,
            use_alternate_screen=True,
            )

        #@self.key_binding_manager.registry.add_binding(Keys.F5)
        #def do_run(event):
        #    pass

    def get_bottom_toolbar_tokens(self, cli):
        return [(Token.Toolbar, 'foobar')]

    def cmdloop(self):
        # self.application.run()
        loop = create_eventloop()
        cli = CommandLineInterface(
            application=self.application, eventloop=loop)
        cli.run()
        return

        while True:
            #cmd = prompt(
            #    '> ',
            #    get_bottom_toolbar_tokens=self.get_bottom_toolbar_tokens,
            #    key_bindings_registry=self.key_binding_manager.registry)
            print(cmd)
            if cmd == 'q':
                break


if __name__ == '__main__':
    # To try out the app:
    from ppci.binutils.dbg.debug_driver import DummyDebugDriver
    PtDebugCli(DummyDebugDriver()).cmdloop()
