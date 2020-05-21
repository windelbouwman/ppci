""" Text writer to create text representation of wasm.
"""
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
        s = "(type %s (func" % typedef.id
        last_anon = False
        for i, param in enumerate(typedef.params):
            id, typ = param
            if isinstance(id, int):
                assert id == i
                if last_anon:
                    s += " " + typ
                else:
                    s += " (param %s" % typ
                    last_anon = True
            else:
                if last_anon:
                    s += ")"
                s += " (param %s %s)" % (id, typ)
                last_anon = False
        s += ")" if last_anon else ""
        if typedef.results:
            s += " (result " + " ".join(typedef.results) + ")"
        return s + "))"

    def write_import_definition(self, imp: components.Import):
        # Get description
        if imp.kind == "func":
            desc = ["(type %s)" % imp.info[0]]
        elif imp.kind == "table":
            desc = ["funcref"]
            if imp.info[2] is not None:
                desc = [str(imp.info[1]), str(imp.info[2]), "funcref"]
            elif imp.info[1] != 0:
                desc = [str(imp.info[1]), "funcref"]
        elif imp.kind == "memory":
            desc = [imp.info[0]] if imp.info[1] is None else list(imp.info)
        elif imp.kind == "global":
            fmt = "(mut %s)" if imp.info[1] else "%s"  # mutable?
            desc = [fmt % imp.info[0]]
        else:  # pragma: no cover
            raise NotImplementedError()

        # Populate description more
        if not (imp.kind in ("memory", "table") and imp.id == "$0"):
            desc.insert(0, imp.id)

        # Compose
        return '(import "%s" "%s" (%s %s))' % (
            imp.modname,
            imp.name,
            imp.kind,
            " ".join(str(i) for i in desc),
        )

    def write_table_definition(self, table: components.Table):
        id = "" if table.id == "$0" else " %s" % table.id
        if table.max is None:
            minmax = "" if table.min == 0 else " %i" % table.min
        else:
            minmax = " %i %i" % (table.min, table.max)
        return "(table%s%s %s)" % (id, minmax, table.kind)

    def write_memory_definition(self, memory: components.Memory):
        id = "" if memory.id == "$0" else " %s" % memory.id
        min = " %i" % memory.min
        max = "" if memory.max is None else " %i" % memory.max
        return "(memory%s%s%s)" % (id, min, max)

    def write_global_definition(self, definition: components.Global):
        init = " ".join(i.to_string() for i in definition.init)
        if definition.mutable:
            return "(global %s (mut %s) %s)" % (
                definition.id,
                definition.typ,
                init,
            )
        else:
            return "(global %s %s %s)" % (definition.id, definition.typ, init)

    def write_func_definition(self, func: components.Func):
        s = ""
        last_anon = False
        for i, local in enumerate(func.locals):
            id, typ = local
            if id is None or isinstance(id, int):
                if id is not None:
                    assert id == i
                if last_anon:
                    s += " " + typ
                else:
                    s += " (local %s" % typ
                    last_anon = True
            else:
                s += ")" if last_anon else ""
                s += " (local %s %s)" % (id, typ)
                last_anon = False
        s += ")" if last_anon else ""
        locals_str = s

        s = "(func %s (type %s)" % (func.id, func.ref) + locals_str + "\n"
        s += self._get_sub_string(func.instructions, True)
        s += "\n)"
        return s

    def write_data_definition(self, datadef: components.Data):
        ref = "" if datadef.ref.is_zero else " %s" % datadef.ref
        offset = " ".join(i.to_string() for i in datadef.offset)
        data_as_str = bytes2datastring(datadef.data)  # repr(self.data)[2:-1]
        return '(data%s %s "%s")' % (ref, offset, data_as_str)

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
