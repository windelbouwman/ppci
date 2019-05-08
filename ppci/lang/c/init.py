""" C initializer helping classes.

The classes and functions here mainly deal with keeping track of the
position in an C style initializer.
"""

import abc
from .nodes import expressions, types


class InitCursor:
    """ A cursor into an arbitrary complex data structure.
    """

    def __init__(self, context):
        self.context = context
        self._stack = []

    def __repr__(self):
        return "InitCursor({})".format(self._stack)

    @property
    def level(self):
        """ The current initial level. """
        return self._stack[-1]

    def at_end(self):
        """ Check if we point the cursor into the void. """
        return self.level.at_end()

    def at_typ(self):
        """ Get the type we are pointing to. """
        return self.level.element_typ()

    def get_value(self):
        """ Get current expression under cursor. """
        return self.level.get_value()

    def set_value(self, value):
        """ Set value at cursor position. """
        self.level.set_value(value)

    def enter_compound(self, typ, location, implicit):
        """ Contrapt new initializer element, and append to stack. """
        is_toplevel = len(self._stack) == 0
        # Get current initializer:
        if is_toplevel:
            initializer = None
        else:
            initializer = self.get_value()

        init_level = self._make_init_level(
            typ, location, initializer, implicit
        )

        if not is_toplevel and not initializer:
            self.set_value(init_level.initializer)

        self._stack.append(init_level)

    def _make_init_level(self, typ, location, initializer, implicit):
        """ Create an initialization level. """
        assert isinstance(typ, types.CType)

        if typ.is_struct:
            if not initializer:
                initializer = expressions.StructInitializer(typ, location)
            init_level = StructInitLevel(initializer, implicit)
        elif typ.is_union:
            if not initializer:
                initializer = expressions.UnionInitializer(typ, location)
            init_level = UnionInitLevel(initializer, implicit)
        else:
            assert typ.is_array

            if typ.size is None:
                size = None
            else:
                size = self.context.eval_expr(typ.size)

            if not initializer:
                initializer = expressions.ArrayInitializer(typ, [], location)

            init_level = ArrayInitLevel(initializer, size, implicit)
        return init_level

    def leave_compound(self):
        """ As in, leave the current sub type.a.b -> type.a """
        return self._stack.pop(-1).initializer

    def unwind(self):
        """ Unwind levels to last explicit level. """
        while self.level.implicit:
            self._stack.pop()

    def next_element(self):
        """ Proceed cursor to next slot to come. """
        # Proceed to next element:
        self.level.go_next()
        while self.level.at_end() and self.level.implicit:
            self.leave_compound()
            self.level.go_next()


class InitLevel(metaclass=abc.ABCMeta):
    """ An in progress initializer. """

    def __init__(self, initializer, implicit):
        self.typ = initializer.typ
        self.initializer = initializer
        self.implicit = implicit

    def element_typ(self):
        """ Current type under cursor. """
        raise NotImplementedError()

    def at_end(self):
        """ Check if there are more elements to be initialized. """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_value(self):
        raise NotImplementedError()

    def set_value(self, value):
        raise NotImplementedError()


class StructInitLevel(InitLevel):
    def __init__(self, initializer, implicit):
        assert initializer.typ.is_struct
        assert isinstance(initializer, expressions.StructInitializer)
        super().__init__(initializer, implicit)
        self.pos = 0  # TODO: integer pos or field name?

    def __repr__(self):
        return "Initializing struct {}, got so far: {}, at pos: {}".format(
            self.typ, self.initializer, self.pos
        )

    def element_typ(self):
        field = self.typ.fields[self.pos]
        return field.typ

    def at_end(self):
        return self.pos >= len(self.typ.fields)

    def go_next(self):
        self.pos += 1

    def go_to_field(self, field):
        pos = self.typ.fields.index(field)
        self.pos = pos

    def get_value(self):
        field = self.typ.fields[self.pos]
        if field in self.initializer.values:
            return self.initializer.values[field]

    def set_value(self, value):
        field = self.typ.fields[self.pos]
        self.initializer.values[field] = value


class UnionInitLevel(InitLevel):
    """ Union initialization in progress. """

    def __init__(self, initializer, implicit):
        assert initializer.typ.is_union
        assert isinstance(initializer, expressions.UnionInitializer)
        super().__init__(initializer, implicit)
        self._field = self.typ.fields[0]
        self._end = False

    def go_to_field(self, field):
        self._field = field
        self._end = False

    def __repr__(self):
        return "Initializing union {}, got so far: {}".format(
            self.typ, self.initializer
        )

    def element_typ(self):
        return self._field.typ

    def at_end(self):
        return self._end

    def go_next(self):
        # Done, contains only one type.
        self._end = True

    def get_value(self):
        return self.initializer.value

    def set_value(self, value):
        self.initializer.field = self._field
        self.initializer.value = value


class ArrayInitLevel(InitLevel):
    """ Array initialization in progress. """

    def __init__(self, initializer, size, implicit):
        assert initializer.typ.is_array
        assert isinstance(initializer, expressions.ArrayInitializer)
        super().__init__(initializer, implicit)
        self.size = size  # Array size
        self.pos = 0  # The position in the array

    def __repr__(self):
        return "Initializing array {} at position {}, got so far: {}".format(
            self.typ, self.pos, self.initializer
        )

    def element_typ(self):
        return self.typ.element_type

    def at_end(self):
        if self.size is None:
            return False
        else:
            return self.pos >= self.size

    def go_to_pos(self, pos):
        self.pos = pos

    def go_next(self):
        self.pos += 1

    def get_value(self):
        if self.pos < len(self.initializer.values):
            return self.initializer.values[self.pos]

    def set_value(self, initial_value):
        # Fill holes:
        while len(self.initializer.values) <= self.pos:
            self.initializer.values.append(None)

        self.initializer.values[self.pos] = initial_value
