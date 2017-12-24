"""
Implements the base Program class and the SourceCodeProgram and
MachineProgram subclasses.
"""

# Registry of program subclasses
_program_subclasses = {}


def get_program_classes():
    """ Get all known Program subclasses as a dictionary: language -> class.
    """
    return _program_subclasses


class ProgramMeta(type):
    """ Meta class to track all subclasses, no matter where they are defined.
    """

    def __init__(cls, name, bases, nmspc):
        super().__init__(name, bases, nmspc)
        n = cls.__name__
        if n:
            if not n.endswith('Program'):
                raise RuntimeError()
            assert n not in _program_subclasses
            # Register subclass
            cls.language = n[:-7].lower()
            _program_subclasses[cls.language] = cls


class Program(object, metaclass=ProgramMeta):
    """
    Abstract base class to represent a computer program. Subclasses represent
    languages (i.e. code representations), e.g. Python, IR, or X86. Program
    objects can be compiled into one another using the ``to_xx()`` methods.

    Each instance can have multiple "items", which can represent files or
    modules, and which can in some cases be bound/linked into a single object.
    Some Program classes also provide optimizations. Many languages can
    be represented in textual or binary form, and can be imported/exported as
    such.

    Each subclass needs to implement:

    * A docstring with a brief description of the language.
    * Method `_check_items(items)` to test input at initialization.
    * Method ``_copy()``.
    * Method ``_get_report(html)``.

    Each subclasses should implement as applicable:

    * Method `optimize()`.
    * Export methods like ``as_text()``.
    * Import classmethods like ``from_text()``.
    """

    def __init__(self, *items, previous=None, debugdb=None):
        if not (previous is None or isinstance(previous, Program)):
            raise TypeError(
                'previous must be None or Program instance.')
        self._previous = previous
        self._items = self._check_items(items)
        # todo: there might be better ways to pass this on
        self.debugdb = debugdb or getattr(previous, 'debugdb', None)

    def _new(self, language, items):
        """ Instatiate a new Program object, with a class specified via its
        corresponding language. This allows ``to_xx()`` methods to function
        without a ref to the target Program class, avoiding circular imports.
        """
        Cls = _program_subclasses[language.lower()]
        return Cls(*items, previous=self, debugdb=self.debugdb)

    def __repr__(self):
        return '<{} with {} items at 0x{}>'.format(
            self.__class__, len(self.items), hex(id(self)))

    @property
    def items(self):
        """ The list of items, representing components such as
        files or modules.
        """
        return self._items

    def previous(self, which=1):
        """ Get a previous Program instance, or None.

        Args:
            which:
                * int: Go this many steps back in the compile chain
                  (default 1).
                * str: Get the program in the compile chain that represents
                  the given language.
                * Program instance/class: Get the program in the compile chain
                  that represents the given Program class.
        """
        # Normalize which arg
        if isinstance(which, Program) or \
                isinstance(which, type) and issubclass(which, Program):
            which = which.language

        # Handle
        if which is None or which == 1:
            return self._previous
        elif isinstance(which, int):
            x = self
            for i in range(which):
                x = x.previous()
            return x
        elif isinstance(which, str):
            x = self
            while x is not None and x.language.lower() != which.lower():
                x = x.previous()
            return x
        else:
            raise TypeError(
                'Program.previous(which) expects int, str'
                ' or Program instance/subclass.')

    @property
    def source(self):
        """ The toplevel Program instance that is the source
        of the compile chain.
        """
        x = self
        while x._previous:
            x = x._previous
        return x

    @property
    def chain(self):
        """ A tuple with the names of the languages that the current object
        originated from.
        """
        chain = []
        x = self
        while x._previous:
            chain.append(x.language)
            x = x._previous
        chain.append(x.language)
        return tuple(reversed(chain))

    # TODO: force specifying in between steps and only compile if path is
    # unique
    def to(self, language, **options):
        """ Compile this program into another representation. The tree is
        traversed to find the lowest cost (i.e. shortest) chain of
        compilers to the target language.

        Experimental; use with care.
        """
        from .graph import mcp
        language = language.lower()
        chain = mcp(self, language)[0]
        if chain is None:
            raise ValueError(
                'No compile chain possible from {} to {}.'.format(
                    self.language, language))
        program = self
        for name in chain[1:-1]:  # skip ourselves
            program = getattr(program, 'to_' + name)()
        program = getattr(program, 'to_' + language)(**options)
        assert isinstance(program, _program_subclasses[language])
        assert program.previous() is not None
        return program

    def copy(self):
        """ Make a (deep) copy of the program.
        """
        return self._copy()

    def get_report(self, html=False):
        """ Get a textual representation of the program for introspection
        and debugging purposes. If ``html`` the report may be html-formatted.
        """
        text = self._get_report(html)
        assert isinstance(text, str)
        return text

    # Methods to overload

    def _check_items(self, items):
        return items

    def _copy(self):
        raise NotImplementedError()

    def _get_report(self, html):
        raise NotImplementedError()


# Classes below mainly serve to categorize languages

class SourceCodeProgram(Program):
    """ Base class for source code.

    (i.e. intended to be read and written by humans).
    """

    def get_tokens(self):
        """ Get the program in the form of a series of (standardized) tokens,
        for the purpose of syntax highlighting.
        """
        # We can couple this to tools that allow writing code for your next
        # experimental language, with syntax highlighting.
        return self._get_tokens()

    def _get_tokens(self):
        raise NotImplementedError()


class IntermediateProgram(Program):
    """ Base class for intermediate code representations.

    These are programs that are not human readable nor machine
    executable.
    """


class MachineProgram(Program):
    """ Base class for executable machine code.
    """

    def run_in_process(self):
        """ If the architecture of the code matches the current machine,
        execute the code in this Python process.
        """
        from ppci.utils import codepage
        # todo: check if arch matches, or does codepage do that?
        native_module = codepage.load_obj(self._items[0])
        return native_module.main()
