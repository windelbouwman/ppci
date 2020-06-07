""" C Statements """

# pylint: disable=R0903


from ...generic.nodes import Node


class CStatement(Node):
    """ Base C statement """

    __slots__ = ("location",)

    def __init__(self, location):
        self.location = location


class Compound(CStatement):
    """ Statement consisting of a sequence of other statements """

    def __init__(self, statements, location):
        super().__init__(location)
        self.statements = statements
        assert all(isinstance(s, CStatement) for s in self.statements)

    def __repr__(self):
        return "Compound"


class If(CStatement):
    """ If statement """

    __slots__ = ("condition", "yes", "no")

    def __init__(self, condition, yes, no, location):
        super().__init__(location)
        self.condition = condition
        self.yes = yes
        self.no = no

    def __repr__(self):
        return "If"


class Switch(CStatement):
    """ Switch statement """

    def __init__(self, expression, statement, location):
        super().__init__(location)
        self.expression = expression
        self.statement = statement

    def __repr__(self):
        return "Switch"


class While(CStatement):
    """ While statement """

    __slots__ = ("condition", "body")

    def __init__(self, condition, body, location):
        super().__init__(location)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return "While"


class DoWhile(CStatement):
    """ Do-while statement """

    __slots__ = ("condition", "body")

    def __init__(self, body, condition, location):
        super().__init__(location)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return "Do-while"


class For(CStatement):
    """ For statement """

    __slots__ = ("init", "condition", "post", "body")

    def __init__(self, init, condition, post, body, location):
        super().__init__(location)
        self.init = init
        self.condition = condition
        self.post = post
        self.body = body

    def __repr__(self):
        return "For"


class Break(CStatement):
    """ Break statement """

    def __repr__(self):
        return "Break"


class Continue(CStatement):
    """ Continue statement """

    def __repr__(self):
        return "Continue"


class Case(CStatement):
    """ Case statement """

    def __init__(self, value, statement, location):
        super().__init__(location)
        self.value = value
        self.statement = statement

    def __repr__(self):
        return "Case"


class RangeCase(CStatement):
    """ GNU Case statement.

    For example:
    'case 1 ... 4:'
    """

    def __init__(self, value1, value2, statement, location):
        super().__init__(location)
        self.value1 = value1
        self.value2 = value2
        self.statement = statement

    def __repr__(self):
        return "Range-Case"


class Default(CStatement):
    """ Default statement """

    def __init__(self, statement, location):
        super().__init__(location)
        self.statement = statement

    def __repr__(self):
        return "Default"


class Label(CStatement):
    """ A label """

    def __init__(self, name, statement, location):
        super().__init__(location)
        self.name = name
        self.statement = statement

    def __repr__(self):
        return "{}:".format(self.name)


class Goto(CStatement):
    """ Goto statement """

    __slots__ = ("label",)

    def __init__(self, label, location):
        super().__init__(location)
        self.label = label

    def __repr__(self):
        return "Goto {}".format(self.label)


class Return(CStatement):
    """ Return statement """

    __slots__ = ("value",)

    def __init__(self, value, location):
        super().__init__(location)
        self.value = value

    def __repr__(self):
        return "Return"


class Empty(CStatement):
    """ Do nothing! """

    def __repr__(self):
        return "Empty"


class ExpressionStatement(CStatement):
    """ An expression used as a statment """

    __slots__ = ("expression",)

    def __init__(self, expression):
        super().__init__(expression.location)
        self.expression = expression

    def __repr__(self):
        return "Expression statement"


class DeclarationStatement(CStatement):
    """ A declaration """

    __slots__ = ("declaration",)

    def __init__(self, declaration, location):
        super().__init__(location)
        self.declaration = declaration

    def __repr__(self):
        return "Declaration statement"


class InlineAssemblyCode(CStatement):
    """ A piece of inlined assembly code """

    def __init__(
        self, template, output_operands, input_operands, clobbers, location
    ):
        super().__init__(location)
        self.template = template
        self.output_operands = output_operands
        self.input_operands = input_operands
        self.clobbers = clobbers

    def __repr__(self):
        return "Inline assembly"


__all__ = [
    "Break",
    "Compound",
    "Continue",
    "Default",
    "DoWhile",
    "For",
    "Goto",
    "If",
    "Return",
    "Switch",
    "While",
]
