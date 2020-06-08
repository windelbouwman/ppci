""" Module to serialize and deserialize IR-code.

Take an IR-module, and turn it into a dict or json.
Then, this item can be persistet or send via e-mail.
Next up, take this dict / json and reconstruct the
identical IR-module from it.

This can be useful in these scenario's:

- Compilation caching: store the IR-code and load from disk when required later on.
- Distributed compilation: transfer IR-code across processes.

.. doctest::

    >>> import io
    >>> from ppci.api import c_to_ir
    >>> from ppci.irutils import to_json, from_json
    >>> c_src = "int add(int a, int b) { return a + b; }"   # Define some C-code
    >>> mod = c_to_ir(io.StringIO(c_src), "x86_64")         # turn C-code into IR-code
    >>> mod.stats()
    'functions: 1, blocks: 1, instructions: 10'
    >>> json_txt = to_json(mod)                             # Turn module into JSON
    >>> mod2 = from_json(json_txt)                          # Load module from JSON.
    >>> mod2.stats()
    'functions: 1, blocks: 1, instructions: 10'


"""
import json
from .. import ir
from ..utils.binary_txt import bin2asc, asc2bin


def to_json(module):
    """ Convert an IR-module to json format.

    Args:
        module: the IR-module intended for serialization.
    
    Returns:
        A JSON string representing the module.
    """
    d = to_dict(module)
    return json.dumps(d, indent=2, sort_keys=True)


def to_dict(module):
    w = DictWriter()
    d = w.write_module(module)
    return d


def from_json(json_txt):
    """ Construct a module from valid json.

    Args:
        json_txt: A string with valid JSON.
    
    Returns:
        The IR-module as represented by JSON.
    """
    return from_dict(json_txt)


def from_dict(d):
    r = DictReader()
    return r.construct(d)


class DictWriter:
    """ Serialize an IR-module as a dict. """

    def __init__(self):
        pass

    def write_module(self, module):
        json_externals = []
        for external in module.externals:
            json_external = self.write_external(external)
            json_externals.append(json_external)

        json_variables = []
        for variable in module.variables:
            json_variable = self.write_variable(variable)
            json_variables.append(json_variable)

        json_functions = []
        for function in module.functions:
            json_function = self.write_subroutine(function)
            json_functions.append(json_function)

        return {
            "name": module.name,
            "externals": json_externals,
            "variables": json_variables,
            "subroutines": json_functions,
        }

    def write_external(self, external):
        if isinstance(external, ir.ExternalVariable):
            json_external = {
                "kind": "variable",
                "name": external.name,
            }
        elif isinstance(external, ir.ExternalFunction):
            json_external = {
                "kind": "function",
                "name": external.name,
                "parameter_types": [
                    self.write_type(ty) for ty in external.argument_types
                ],
                "return_type": self.write_type(external.return_ty),
            }
        elif isinstance(external, ir.ExternalProcedure):
            json_external = {
                "kind": "procedure",
                "name": external.name,
                "parameter_types": [
                    self.write_type(ty) for ty in external.argument_types
                ],
            }
        else:  # pragma: no cover
            raise NotImplementedError(str(external))
        return json_external

    def write_binding(self, binding):
        return str(binding)

    def write_variable(self, variable):
        if isinstance(variable, ir.Variable):
            json_variable = {
                "name": variable.name,
                "binding": self.write_binding(variable.binding),
                "amount": variable.amount,
                "alignment": variable.alignment,
            }
        else:  # pragma: no cover
            raise NotImplementedError(str(variable))
        return json_variable

    def write_subroutine(self, subroutine):
        json_binding = self.write_binding(subroutine.binding)
        json_parameters = []
        for parameter in subroutine.arguments:
            json_parameter = {
                "name": parameter.name,
                "type": self.write_type(parameter.ty),
            }
            json_parameters.append(json_parameter)

        json_blocks = []
        for block in subroutine.blocks:
            json_block = self.write_block(block)
            json_blocks.append(json_block)

        json_subroutine = {
            "binding": json_binding,
            "name": subroutine.name,
            "parameters": json_parameters,
            "blocks": json_blocks,
        }

        if isinstance(subroutine, ir.Function):
            json_subroutine["kind"] = "function"
            json_subroutine["return_type"] = self.write_type(
                subroutine.return_ty
            )
        else:
            assert isinstance(subroutine, ir.Procedure)
            json_subroutine["kind"] = "procedure"
        return json_subroutine

    def write_block(self, block):
        json_instructions = []
        for instruction in block.instructions:
            json_instruction = self.write_instruction(instruction)
            json_instructions.append(json_instruction)
        json_block = {
            "name": block.name,
            "instructions": json_instructions,
        }
        return json_block

    def write_instruction(self, instruction):
        if isinstance(instruction, ir.Load):
            json_instruction = {
                "kind": "load",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "address": self.write_value_ref(instruction.address),
                "volatile": instruction.volatile,
            }
        elif isinstance(instruction, ir.Store):
            json_instruction = {
                "kind": "store",
                "address": self.write_value_ref(instruction.address),
                "value": self.write_value_ref(instruction.value),
                "volatile": instruction.volatile,
            }
        elif isinstance(instruction, ir.Alloc):
            json_instruction = {
                "kind": "alloc",
                "type": self.write_type(instruction.ty),
                "size": instruction.amount,
                "alignment": instruction.alignment,
                "name": instruction.name,
            }
        elif isinstance(instruction, ir.Binop):
            json_instruction = {
                "kind": "binop",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "a": self.write_value_ref(instruction.a),
                "operation": instruction.operation,
                "b": self.write_value_ref(instruction.b),
            }
        elif isinstance(instruction, ir.Unop):
            json_instruction = {
                "kind": "unop",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "a": self.write_value_ref(instruction.a),
                "operation": instruction.operation,
            }
        elif isinstance(instruction, ir.AddressOf):
            json_instruction = {
                "kind": "addressof",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "src": self.write_value_ref(instruction.src),
            }
        elif isinstance(instruction, ir.Exit):
            json_instruction = {
                "kind": "exit",
            }
        elif isinstance(instruction, ir.Return):
            json_instruction = {
                "kind": "return",
                "result": self.write_value_ref(instruction.result),
            }
        elif isinstance(instruction, ir.Jump):
            json_instruction = {
                "kind": "jump",
                "target": self.write_block_ref(instruction.target),
            }
        elif isinstance(instruction, ir.CJump):
            json_instruction = {
                "kind": "cjump",
                "a": self.write_value_ref(instruction.a),
                "b": self.write_value_ref(instruction.b),
                "condition": instruction.cond,
                "yes_block": self.write_block_ref(instruction.lab_yes),
                "no_block": self.write_block_ref(instruction.lab_no),
            }
        elif isinstance(instruction, ir.Cast):
            json_instruction = {
                "kind": "cast",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "value": self.write_value_ref(instruction.src),
            }
        elif isinstance(instruction, ir.Const):
            json_instruction = {
                "kind": "const",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "value": instruction.value,
            }
        elif isinstance(instruction, ir.LiteralData):
            json_instruction = {
                "kind": "literaldata",
                "name": instruction.name,
                "data": bin2asc(instruction.data),
            }
        elif isinstance(instruction, ir.ProcedureCall):
            json_arguments = [
                self.write_value_ref(argument)
                for argument in instruction.arguments
            ]
            json_instruction = {
                "kind": "procedurecall",
                "callee": self.write_value_ref(instruction.callee),
                "arguments": json_arguments,
            }
        elif isinstance(instruction, ir.FunctionCall):
            json_arguments = [
                self.write_value_ref(argument)
                for argument in instruction.arguments
            ]
            json_instruction = {
                "kind": "functioncall",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "callee": self.write_value_ref(instruction.callee),
                "arguments": json_arguments,
            }
        elif isinstance(instruction, ir.Phi):
            json_phi_inputs = []
            for phi_input_block, phi_input_value in instruction.inputs.items():
                json_phi_input = {
                    "block": self.write_block_ref(phi_input_block),
                    "value": self.write_value_ref(phi_input_value),
                }
                json_phi_inputs.append(json_phi_input)

            json_instruction = {
                "kind": "phi",
                "name": instruction.name,
                "type": self.write_type(instruction.ty),
                "inputs": json_phi_inputs,
            }
        else:  # pragma: no cover
            raise NotImplementedError(str(instruction))
        return json_instruction

    def write_type(self, ty):
        if isinstance(ty, (ir.BasicTyp, ir.PointerTyp)):
            json_type = {
                "kind": "basic",
                "name": ty.name,
            }
        elif isinstance(ty, ir.BlobDataTyp):
            json_type = {
                "kind": "blob",
                "size": ty.size,
                "alignment": ty.alignment,
            }
        else:  # pragma: no cover
            raise NotImplementedError(str(ty))
        return json_type

    def write_value_ref(self, value):
        return value.name

    def write_block_ref(self, block):
        return block.name


class Scope:
    def __init__(self):
        self.value_map = {}
        self.block_map = {}


class DictReader:
    """ Construct IR-module from given json.
    """

    def __init__(self):
        # self.subroutines = []
        self.scopes = []
        self.undefined_values = {}

    def construct(self, json_txt):
        d = json.loads(json_txt)
        name = d["name"]
        json_externals = d["externals"]
        json_variables = d["variables"]
        json_subroutines = d["subroutines"]

        self.enter_scope()

        module = ir.Module(name)

        for json_external in json_externals:
            external = self.construct_external(json_external)
            module.add_external(external)

        for json_variable in json_variables:
            variable = self.construct_variable(json_variable)
            module.add_variable(variable)

        for json_subroutine in json_subroutines:
            subroutine = self.construct_subroutine(json_subroutine)
            module.add_function(subroutine)

        assert not self.undefined_values
        self.leave_scope()

        return module

    def construct_external(self, json_external):
        etype = json_external["kind"]
        name = json_external["name"]
        if etype == "variable":
            external = ir.ExternalVariable(name)
        elif etype == "function":

            argument_types = [
                self.get_type(pt) for pt in json_external["parameter_types"]
            ]
            return_type = self.get_type(json_external["return_type"])
            external = ir.ExternalFunction(name, argument_types, return_type)
        elif etype == "procedure":
            argument_types = [
                self.get_type(pt) for pt in json_external["parameter_types"]
            ]
            external = ir.ExternalProcedure(name, argument_types)
        else:  # pragma: no cover
            raise NotImplementedError(etype)
        self.register_value(external)
        return external

    def construct_binding(self, json_binding):
        bindings = {
            "local": ir.Binding.LOCAL,
            "global": ir.Binding.GLOBAL,
        }
        binding = bindings[json_binding]
        return binding

    def construct_variable(self, json_variable):
        name = json_variable["name"]
        binding = self.construct_binding(json_variable["binding"])
        amount = json_variable["amount"]
        alignment = json_variable["alignment"]
        variable = ir.Variable(name, binding, amount, alignment)
        self.register_value(variable)
        return variable

    def construct_subroutine(self, json_subroutine):
        name = json_subroutine["name"]
        json_blocks = json_subroutine["blocks"]
        json_parameters = json_subroutine["parameters"]
        binding = self.construct_binding(json_subroutine["binding"])
        stype = json_subroutine["kind"]

        if stype == "function":
            return_type = self.get_type(json_subroutine["return_type"])
            subroutine = ir.Function(name, binding, return_type)
        elif stype == "procedure":
            subroutine = ir.Procedure(name, binding)
        else:  # pragma: no cover
            raise NotImplementedError(stype)
        self.register_value(subroutine)

        # self.subroutines.append(subroutine)
        self.enter_scope()
        for json_parameter in json_parameters:
            name = json_parameter["name"]
            ty = self.get_type(json_parameter["type"])
            parameter = ir.Parameter(name, ty)
            self.register_value(parameter)
            subroutine.add_parameter(parameter)

        for json_block in json_blocks:
            block = self.construct_block(json_block, subroutine)
            if subroutine.entry is None:
                subroutine.entry = block
            subroutine.add_block(block)
        self.leave_scope()
        # self.subroutines.pop()
        return subroutine

    def construct_block(self, json_block, subroutine):
        name = json_block["name"]
        json_instructions = json_block["instructions"]
        block = self.new_block(name, subroutine)
        for json_instruction in json_instructions:
            instruction = self.construct_instruction(json_instruction)
            block.add_instruction(instruction)
        return block

    def construct_instruction(self, json_instruction):
        itype = json_instruction["kind"]
        if itype == "load":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            address = self.get_value_ref(json_instruction["address"])
            instruction = ir.Load(address, name, ty)
            self.register_value(instruction)
        elif itype == "store":
            value = self.get_value_ref(json_instruction["value"])
            address = self.get_value_ref(json_instruction["address"])
            instruction = ir.Store(value, address)
        elif itype == "alloc":
            name = json_instruction["name"]
            amount = json_instruction["size"]
            alignment = json_instruction["alignment"]
            instruction = ir.Alloc(name, amount, alignment)
            self.register_value(instruction)
        elif itype == "addressof":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            src = self.get_value_ref(json_instruction["src"])
            instruction = ir.AddressOf(src, name)
            self.register_value(instruction)
        elif itype == "binop":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            a = self.get_value_ref(json_instruction["a"])
            operation = json_instruction["operation"]
            b = self.get_value_ref(json_instruction["b"])
            instruction = ir.Binop(a, operation, b, name, ty)
            self.register_value(instruction)
        elif itype == "unop":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            a = self.get_value_ref(json_instruction["a"])
            operation = json_instruction["operation"]
            instruction = ir.Unop(operation, a, name, ty)
            self.register_value(instruction)
        elif itype == "cast":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            value = self.get_value_ref(json_instruction["value"])
            instruction = ir.Cast(value, name, ty)
            self.register_value(instruction)
        elif itype == "const":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            value = json_instruction["value"]
            instruction = ir.Const(value, name, ty)
            self.register_value(instruction)
        elif itype == "literaldata":
            name = json_instruction["name"]
            data = asc2bin(json_instruction["data"])
            instruction = ir.LiteralData(data, name)
            self.register_value(instruction)
        elif itype == "phi":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            instruction = ir.Phi(name, ty)
            for json_phi_input in json_instruction["inputs"]:
                instruction.set_incoming(
                    self.get_block_ref(json_phi_input["block"]),
                    self.get_value_ref(json_phi_input["value"], ty=ty),
                )
            self.register_value(instruction)
        elif itype == "jump":
            target = self.get_block_ref(json_instruction["target"])
            instruction = ir.Jump(target)
        elif itype == "cjump":
            a = self.get_value_ref(json_instruction["a"])
            cond = json_instruction["condition"]
            b = self.get_value_ref(json_instruction["b"])
            lab_yes = self.get_block_ref(json_instruction["yes_block"])
            lab_no = self.get_block_ref(json_instruction["no_block"])
            instruction = ir.CJump(a, cond, b, lab_yes, lab_no)
        elif itype == "procedurecall":
            callee = self.get_value_ref(json_instruction["callee"])
            arguments = []
            for json_argument in json_instruction["arguments"]:
                arguments.append(self.get_value_ref(json_argument))
            instruction = ir.ProcedureCall(callee, arguments)
        elif itype == "functioncall":
            name = json_instruction["name"]
            ty = self.get_type(json_instruction["type"])
            callee = self.get_value_ref(json_instruction["callee"])
            arguments = []
            for json_argument in json_instruction["arguments"]:
                arguments.append(self.get_value_ref(json_argument))
            instruction = ir.FunctionCall(callee, arguments, name, ty)
            self.register_value(instruction)
        elif itype == "exit":
            instruction = ir.Exit()
        elif itype == "return":
            result = self.get_value_ref(json_instruction["result"])
            instruction = ir.Return(result)
        else:  # pragma: no cover
            raise NotImplementedError(itype)
        return instruction

    def get_type(self, json_type):
        tkind = json_type["kind"]
        if tkind == "basic":
            typ_map = {ty.name: ty for ty in ir.all_types}
            typ = typ_map[json_type["name"]]
        elif tkind == "blob":
            size = json_type["size"]
            alignment = json_type["alignment"]
            typ = ir.BlobDataTyp(size, alignment)
        else:  # pragma: no cover
            raise NotImplementedError(tkind)
        return typ

    def register_value(self, value):
        if value.name in self.undefined_values:
            old_value = self.undefined_values.pop(value.name)
            old_value.replace_by(value)
        assert value.name not in self.scopes[-1].value_map
        self.scopes[-1].value_map[value.name] = value

    def get_value_ref(self, name, ty=ir.ptr):
        """ Retrieve reference to a value.
        """
        for scope in reversed(self.scopes):
            if name in scope.value_map:
                value = scope.value_map[name]
                break
        else:
            if name in self.undefined_values:
                value = self.undefined_values[name]
            else:
                value = ir.Undefined(name, ty)
                self.undefined_values[name] = value
        return value

    def enter_scope(self):
        self.scopes.append(Scope())

    def leave_scope(self):
        self.scopes.pop()

    # def register_block(self, block):
    #     if block.name in self.block_map:
    #         #block.replace_incoming()
    #         old_block = self.block_map[block.name]
    #         old_block.replace_by(block)

    #     self.block_map[block.name] = block

    def new_block(self, name, subroutine):
        if name in self.scopes[-1].block_map:
            block = self.scopes[-1].block_map[name]
            assert block.function is None
        else:
            block = ir.Block(name)
            self.scopes[-1].block_map[name] = block

        block.function = subroutine
        return block

    def get_block_ref(self, name):
        if name in self.scopes[-1].block_map:
            block = self.scopes[-1].block_map[name]
        else:
            block = ir.Block(name)
            self.scopes[-1].block_map[name] = block
        return block
