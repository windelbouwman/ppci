""" Text writer to create text representation of wasm.
"""
import io
from .. import components
from .util import default_alignment, bytes2datastring


class TextWriter:
    """ A writer for the wasm text format.

    This is the reverse of the text parser.

    Some ideas which can/will be implemented here:
    - set a global indentation
    - emit tokens, and construct text, or tuples from those tokens.
    """

    def __init__(self, indentation=2):
        self.indentation = indentation
        self._f = io.StringIO()
        self._last = None

    def write_module(self, module: components.Module):
        # TODO: idea: first construct tuples, then pretty print these tuples
        # to strings.
        id_str = " " + module.id if module.id else ""
        if module.definitions:
            defs_str = "\n%s\n" % self._get_sub_string(
                module.definitions, True
            )
        else:
            defs_str = ""
        return "(module" + id_str + defs_str + ")\n"

    def write_type_definition(self, typedef: components.Type):
        self.emit("(", "type")
        self.gen_id(typedef.id)
        self.emit("(", "func")

        last_anon = False
        for i, param in enumerate(typedef.params):
            id, typ = param
            if isinstance(id, int):
                assert id == i
                if last_anon:
                    self.emit(str(typ))
                else:
                    self.emit("(", "param", str(typ))
                    last_anon = True
            else:
                if last_anon:
                    self.emit(")")
                self.emit("(", "param", str(id), str(typ), ")")
                last_anon = False

        if last_anon:
            self.emit(")")

        if typedef.results:
            self.emit("(", "result")
            for r in typedef.results:
                self.emit(str(r))
            self.emit(")")
        self.emit(")", ")")

    def write_import_definition(self, imp: components.Import):
        self.emit("(", "import", '"%s"' % imp.modname, '"%s"' % imp.name)
        self.emit("(", "%s" % imp.kind)
        # Get description
        if imp.kind == "func":
            self.gen_id(imp.id)
            self.emit("(", "type", str(imp.info[0]), ")")
        elif imp.kind == "table":
            if imp.id != "$0":
                self.gen_id(imp.id)

            if imp.info[2] is not None:
                self.emit(str(imp.info[1]), str(imp.info[2]))
            elif imp.info[1] != 0:
                self.emit(str(imp.info[1]))
            self.emit("funcref")
        elif imp.kind == "memory":
            if imp.id != "$0":
                self.gen_id(imp.id)

            self.emit(str(imp.info[0]))
            if imp.info[1] is not None:
                self.emit(str(imp.info[1]))
        elif imp.kind == "global":
            self.gen_id(imp.id)
            if imp.info[1]:
                # mutable
                self.emit("(", "mut", str(imp.info[0]), ")")
            else:
                self.emit(str(imp.info[0]))
        else:  # pragma: no cover
            raise NotImplementedError()

        self.emit(")", ")")

    def write_table_definition(self, table: components.Table):
        self.emit("(", "table")
        self.gen_id(table.id)
        if table.max is None:
            if table.min != 0:
                self.emit("%i" % table.min)
        else:
            self.emit("%i" % table.min)
            self.emit("%i" % table.max)
        self.emit(table.kind)
        self.emit(")")

    def write_memory_definition(self, memory: components.Memory):
        self.emit("(", "memory")
        self.gen_id(memory.id)
        self.emit("%i" % memory.min)
        if memory.max is not None:
            self.emit("%i" % memory.max)
        self.emit(")")

    def write_global_definition(self, definition: components.Global):
        self.emit("(", "global")
        self.gen_id(definition.id)
        if definition.mutable:
            self.emit("(", "mut", str(definition.typ), ")")
        else:
            self.emit(str(definition.typ))
        init = " ".join(i.to_string() for i in definition.init)
        self.emit(init)
        self.emit(")")

    def write_func_definition(self, func: components.Func):
        self.emit("(", "func")
        self.gen_id(func.id)
        self.emit("(", "type", str(func.ref), ")")
        self.emit("\n")

        if func.locals:
            self.emit(" ")
            last_anon = False
            for i, local in enumerate(func.locals):
                id, typ = local
                if id is None or isinstance(id, int):
                    if id is not None:
                        assert id == i
                    if last_anon:
                        self.emit(str(typ))
                    else:
                        self.emit("(", "local", str(typ))
                        last_anon = True
                else:
                    if last_anon:
                        self.emit(")")
                    self.emit("(", "local", str(id), str(typ), ")")
                    last_anon = False
            if last_anon:
                self.emit(")")

            self.emit("\n")

        self.emit(self._get_sub_string(func.instructions, True))
        self.emit(")")

    def write_elem_definition(self, elemdef: components.Elem):
        self.emit("(", "elem")
        if not elemdef.ref.is_zero:
            self.emit(str(elemdef.ref))
        offset = " ".join(i.to_string() for i in elemdef.offset)
        self.emit(offset)
        for i in elemdef.refs:
            self.emit(str(i))
        self.emit(")")

    def write_data_definition(self, datadef: components.Data):
        self.emit("(", "data")
        if not datadef.ref.is_zero:
            self.emit(str(datadef.ref))
        # self.emit(' ')
        # self.gen_id(datadef.id)
        offset = " ".join(i.to_string() for i in datadef.offset)
        self.emit(offset)
        self.emit('"' + bytes2datastring(datadef.data) + '"')
        self.emit(")")

    def write_instruction(self, instruction: components.Instruction):
        opcode = instruction.opcode
        args = instruction.args
        if ".load" in opcode or ".store" in opcode:
            align, offset = args
            args = []
            if offset:
                args.append("offset=%i" % offset)

            if align != default_alignment(opcode):
                args.append("align=%i" % 2 ** align)

            args = tuple(args)

        elif opcode == "br_table":
            tab = args[0]
            args = [str(t) for t in tab]

        elif opcode == "memory.size" or opcode == "memory.grow":
            # TODO: this argument might be used some day..
            args = []

        elif opcode == "call_indirect":
            if args[1].index == 0:  # zero'th table
                args = ("(type %s)" % args[0],)
            else:
                args = (
                    "(type %s)" % args[0],
                    "(const.i64 %i)" % args[1].index,
                )
        subtext = self._get_sub_string(args)
        if "\n" in subtext:
            return "(" + opcode + "\n" + subtext + "\n)"
        else:
            return opcode + " " * bool(subtext) + subtext

    def write_block_instruction(
        self, instruction: components.BlockInstruction
    ):
        opcode = instruction.opcode
        idtext = "" if instruction.id is None else " " + instruction.id
        a0 = instruction.args[0]
        if a0 == "emptyblock":
            subtext = ""
        else:
            subtext = " (result {})".format(a0)
        return opcode + idtext + subtext

    def _get_sub_string(self, subs, multiline=False):
        """ Helper method to get the string of a list of sub components,
        inserting newlines as needed.
        """
        # Collect sub texts
        texts = []
        charcount = 0
        haslf = False
        for sub in subs:
            if isinstance(sub, components.WASMComponent):
                text = sub.to_string()
            else:
                text = str(sub)  # or repr ...
            charcount += len(text)
            texts.append(text)
            haslf = haslf or "\n" in text
        # Put on one line or multiple lines
        if multiline or haslf or charcount > 70:
            lines = []
            indent_size = 2
            indent = indent_size
            for text in texts:
                for line in text.splitlines():
                    if line.startswith(("else", "end")):
                        indent -= indent_size
                    lines.append(" " * indent + line)
                    if line.startswith(("block", "loop", "if", "else")):
                        indent += indent_size
            return "\n".join(lines)
        else:
            return " ".join(texts)

    def gen_id(self, id):
        if isinstance(id, int):
            self.comment(str(id))
        else:
            self.emit(str(id))

    def comment(self, txt):
        """ Emit commented text. """
        self.emit("(;" + txt + ";)")

    def emit(self, *txts):
        """ Write text.

        Idea: have different handlers for text creation and tuple creation.
        """
        for txt in txts:
            if not (
                self._last is None
                or self._last == "("
                or txt == ")"
                or txt == "\n"
                or self._last == "\n"
            ):
                self._f.write(" ")
            self._f.write(txt)
            self._last = txt

    def finish(self):
        """ Wrap up and return emitted text. """
        return self._f.getvalue()
