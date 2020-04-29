""" Befunge support.

Epic esotheric language in 2D!

See also: https://en.wikipedia.org/wiki/Befunge

"""

hello_world = """\
>25*"!dlrow ,olleH":v
                 v:,_@
                 >  ^
"""

quine = """01->1# +# :# 0# g# ,# :# 5# 8# *# 4# +# -# _@"""


def run_befunge(src):
    """ Execute a slab of befunge.
    """
    print("parsing", src)
    lines = src.splitlines()

    m = BefungeInterpreter(lines)
    m.run()


class BefungeInterpreter:
    """ Befunge machine. """

    def __init__(self, code):
        self.verbose = False
        self.load_code(code)
        self.reset()

    def load_code(self, code):
        self.code = code
        self.x_max = max(len(line) for line in code) - 1
        self.y_max = len(code) - 1

    def reset(self):
        """ Reset machine state """
        self.stack = []
        self.x = 0
        self.y = 0
        self.string_mode = False
        self.skip = False
        self.dx = 1
        self.dy = 0
        self.running = True

    def run(self):
        """ Run until finished. """
        while self.running:
            self.single_step()

    def single_step(self):
        """ Execute a single opcode. """
        op = self.fetch()
        if self.verbose:
            print("at", self.y, self.x, "execute", op)

        if self.string_mode:
            if op == '"':
                self.string_mode = False
            else:
                self.push(ord(op))
        elif self.skip:  # bridge instruction.
            self.skip = False
        else:
            self.dispatch(op)

        self.move_pointer()

    def move_pointer(self):
        self.x += self.dx
        if self.x < 0:
            self.x = self.x_max
        elif self.x > self.x_max:
            self.x = 0

        self.y += self.dy
        if self.y < 0:
            self.y = self.y_max
        elif self.y > self.y_max:
            self.y = 0

    def fetch(self):
        return self.get(self.y, self.x)

    def get(self, row, column):
        """ Get character at position """
        line = self.code[row]
        if column < len(line):
            return line[column]
        else:
            return " "

    def put(self, row, column, value):
        """ Enable self modifying code! """
        raise NotImplementedError()

    def dispatch(self, op):
        """ Execute a single opcode. """
        if op in "0123456789":
            self.push(int(op))
        elif op == "+":
            self.push(self.pop() + self.pop())
        elif op == "-":
            self.push(self.pop() - self.pop())
        elif op == "*":
            self.push(self.pop() * self.pop())
        elif op == "/":
            self.push(self.pop() // self.pop())
        elif op == "%":
            self.push(self.pop() % self.pop())
        elif op == "!":  # logical not
            self.push(1 if self.pop() == 0 else 0)
        elif op == "`":  # greater than
            self.push(1 if self.pop() > self.pop() else 0)
        elif op == ">":
            self.go_right()
        elif op == "<":
            self.go_left()
        elif op == "^":
            self.go_up()
        elif op == "v":
            self.go_down()
        elif op == "?":  # Random direction!
            raise NotImplementedError()
        elif op == "_":  # go left or right
            if self.pop() == 0:
                self.go_right()
            else:
                self.go_left()
        elif op == "|":  # go up or down
            if self.pop() == 0:
                self.go_down()
            else:
                self.go_up()
        elif op == '"':  # Enable string mode!
            self.string_mode = True
        elif op == ":":  # Duplicate top of stack
            value = self.pop()
            self.push(value)
            self.push(value)
        elif op == "\\":
            a, b = self.pop(), self.pop()
            self.push(a)
            self.push(b)
        elif op == "$":  # Drop top of stack
            self.pop()
        elif op == ".":  # output number
            value = self.pop()
            print(value, end=" ")
        elif op == ",":  # output char
            value = self.pop()
            print(chr(value), end="")
        elif op == "#":  # Skip next cell!
            self.skip = True
        elif op == "p":
            raise NotImplementedError()
        elif op == "g":
            y, x = self.pop(), self.pop()
            self.push(ord(self.get(y, x)))
        elif op == "&":  # ask number as input
            raise NotImplementedError()
        elif op == "@":  # end program
            self.running = False
        elif op == " ":  # no-op
            pass
        else:
            raise NotImplementedError("Invalid opcode: {}".format(op))

    def go_left(self):
        self.dx, self.dy = -1, 0

    def go_right(self):
        self.dx, self.dy = 1, 0

    def go_up(self):
        self.dx, self.dy = 0, -1

    def go_down(self):
        self.dx, self.dy = 0, 1

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if self.stack:
            return self.stack.pop()
        else:
            return 0


def compile_befunge(src):
    pass


run_befunge(hello_world)
# run_befunge(quine)
