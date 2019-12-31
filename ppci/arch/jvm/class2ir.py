""" Functionality to translate a java class file into ir-code.
"""

import logging
from .io import load_code, parse_method_descriptor
from .nodes import BaseType
from .enums import AccessFlag, ConstantTag
from ...binutils import debuginfo
from ...common import SourceLocation
from ...irutils import Builder
from ... import ir


logger = logging.getLogger("jvm2ir")


def class_to_ir(class_file):
    """ Translate java class file into IR-code. """
    generator = Generator()
    generator.initialize()
    generator.gen_class(class_file)
    return generator.get_result()


def jar_to_ir(jar_file):
    """ Translate entire jar to ir code. """
    generator = Generator()
    generator.initialize()

    for class_file in jar_file:
        generator.gen_class(class_file)

    return generator.get_result()


class Generator:
    def __init__(self):
        self._builder = Builder()
        self.stack = None
        self.local_variables = None
        self.class_file = None

    def initialize(self):
        """ Prepare translation. """
        self.debug_db = debuginfo.DebugDb()
        module = ir.Module("java", debug_db=self.debug_db)
        self._builder.set_module(module)

    def emit(self, instr):
        return self._builder.emit(instr)

    def get_ir_type(self, typ):
        if isinstance(typ, BaseType):
            mp = {
                "B": ir.i8,
                "S": ir.i16,
                "I": ir.i32,
                "F": ir.f32,
                "D": ir.f64,
            }
            return mp[typ.typ]
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def get_debug_type(self, typ):
        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)
        else:
            if isinstance(typ, BaseType):
                dbg_type_map = {
                    "F": debuginfo.DebugBaseType("float", 4, 1),
                    "D": debuginfo.DebugBaseType("double", 8, 1),
                    "I": debuginfo.DebugBaseType("int", 4, 1),
                    "J": debuginfo.DebugBaseType("long", 8, 1),
                    "V": debuginfo.DebugBaseType("void", 0, 1),
                }
                dbg_typ = dbg_type_map[typ.typ]
                self.debug_db.enter(typ, dbg_typ)
                return dbg_typ
            else:  # pragma: no cover
                raise NotImplementedError(str(typ))

    def get_result(self):
        return self._builder.module

    def gen_class(self, class_file):
        logger.warning("java class file code generate is work in progress")
        self._functions = {}
        self.class_file = class_file
        for method in class_file.methods:
            if AccessFlag.ACC_STATIC in method.access_flags:
                self.gen_method(method)
            else:
                logger.warning("Skipping non-static function %s", method.name)

    def gen_method(self, method):
        """ Generate code for a single method. """
        logger.info(
            "processing method %s access=%s", method.name, method.access_flags
        )

        signature = method.descriptor
        logger.debug("Descriptor: %s", signature)

        # Construct valid function:
        binding = ir.Binding.GLOBAL
        if signature.return_type:
            ir_typ = self.get_ir_type(signature.return_type)
            ir_func = self._builder.new_function(method.name, binding, ir_typ)
            dbg_return_type = self.get_debug_type(signature.return_type)
        else:
            ir_func = self._builder.new_procedure(method.name, binding)
            dbg_return_type = debuginfo.DebugBaseType("void", 0, 1)
        self._builder.set_function(ir_func)

        # Register function:
        if method.name in self._functions:
            # Maybe we had an external function at first?
            raise NotImplementedError("TODO: update existing / replace?")
        else:
            self._functions[method.name] = ir_func

        # Start in entry block:
        first_block = self._builder.new_block()
        self._builder.set_block(first_block)
        ir_func.entry = first_block

        dbg_arg_types = []
        self.local_variables = []

        logger.debug("Signature: %s", signature.parameter_types)
        for index, parameter_type in enumerate(signature.parameter_types):
            ir_typ = self.get_ir_type(parameter_type)
            parameter_name = "param{}".format(index)
            ir_parameter = ir.Parameter(parameter_name, ir_typ)
            ir_func.add_parameter(ir_parameter)
            dbg_arg_types.append(
                debuginfo.DebugParameter(
                    "arg{}".format(index), self.get_debug_type(parameter_type)
                )
            )

            # Create local variable, and store parameter:
            size = 8  # TODO: fetch this from elsewhere.
            alignment = 8
            alloc_param = self.emit(ir.Alloc("alloc", size, alignment))
            param_ptr = self.emit(ir.AddressOf(alloc_param, "ptr"))
            self.emit(ir.Store(ir_parameter, param_ptr))
            logger.debug("adding local %s", param_ptr)
            self.local_variables.append(param_ptr)

        # Enter correct debug info:
        db_function_info = debuginfo.DebugFunction(
            ir_func.name,
            SourceLocation("somefile.java", 1, 1, 1),
            dbg_return_type,
            dbg_arg_types,
        )
        self.debug_db.enter(ir_func, db_function_info)

        for attribute in method.attributes:
            attrib_name = attribute.name
            if attrib_name == "Code":
                # Now we found bytecode.
                code = load_code(attribute.data)
                self.gen_code(code)
            else:
                logger.warning("Unhandled attribute: %s", attrib_name)

        # Assume we returned in one way or another?
        # if signature.return_type:
        #    value = self.stack.pop()
        #    self.emit(ir.Return(value))
        # else:
        #    self.emit(ir.Exit())

    def gen_code(self, code):
        logger.debug(
            "Max stack=%s, max locals=%s", code.max_stack, code.max_locals
        )

        # print(code.attributes)
        for index in range(code.max_locals):
            size = 8  # TODO: fetch this from elsewhere.
            alignment = 8
            alloc_local = self.emit(ir.Alloc("alloc", size, alignment))
            local_ptr = self.emit(ir.AddressOf(alloc_local, "ptr"))
            self.local_variables.append(local_ptr)

        self.stack = []
        for instruction in code.code:
            self.gen_instr(instruction)

    def gen_instr(self, instruction):
        """ Generate ir-code for a single instruction. """
        mnemonic = instruction.mnemonic
        # op_to_name[instruction]  # .opcode
        args = instruction.args
        # [0, 1, 2, 3]  # ?
        logger.debug("processing %s", instruction)

        # Start of a giant if-tree with all opcodes:
        if mnemonic == "nop":
            pass  # Relaxation time!
        elif mnemonic == "iconst_m1":
            self.gen_load_const(-1, ir.i32)
        elif mnemonic == "iconst_0":
            self.gen_load_const(0, ir.i32)
        elif mnemonic == "iconst_1":
            self.gen_load_const(1, ir.i32)
        elif mnemonic == "iconst_2":
            self.gen_load_const(2, ir.i32)
        elif mnemonic == "iconst_3":
            self.gen_load_const(3, ir.i32)
        elif mnemonic == "iconst_4":
            self.gen_load_const(4, ir.i32)
        elif mnemonic == "iconst_5":
            self.gen_load_const(5, ir.i32)
        elif mnemonic == "lconst_0":
            self.gen_load_const(0, ir.i64)
        elif mnemonic == "lconst_1":
            self.gen_load_const(1, ir.i64)
        elif mnemonic == "fconst_0":
            self.gen_load_const(0, ir.f32)
        elif mnemonic == "fconst_1":
            self.gen_load_const(1, ir.f32)
        elif mnemonic == "fconst_2":
            self.gen_load_const(2, ir.f32)
        elif mnemonic == "dconst_0":
            self.gen_load_const(0, ir.f64)
        elif mnemonic == "dconst_1":
            self.gen_load_const(1, ir.f64)
        elif mnemonic == "bipush":
            value = args[0]
            self.gen_load_const(value, ir.i32)
        elif mnemonic == "sipush":
            value = args[0]
            self.gen_load_const(value, ir.i32)
        elif mnemonic == "ldc":
            index = args[0]
            value = self.class_file.constant_pool[index]
            typ_map = {ConstantTag.Float: ir.f32, ConstantTag.Integer: ir.i32}
            typ = typ_map[value.tag]
            value = value.value
            self.gen_load_const(value, typ)
        elif mnemonic == "iload":
            index = args[0]
            self.gen_load_local(index, ir.i32)
        elif mnemonic == "lload":
            index = args[0]
            self.gen_load_local(index, ir.i64)
        elif mnemonic == "fload":
            index = args[0]
            self.gen_load_local(index, ir.f32)
        elif mnemonic == "dload":
            index = args[0]
            self.gen_load_local(index, ir.f64)
        elif mnemonic == "iload_0":
            self.gen_load_local(0, ir.i32)
        elif mnemonic == "iload_1":
            self.gen_load_local(1, ir.i32)
        elif mnemonic == "iload_2":
            self.gen_load_local(2, ir.i32)
        elif mnemonic == "iload_3":
            self.gen_load_local(3, ir.i32)
        elif mnemonic == "lload_0":
            self.gen_load_local(0, ir.i64)
        elif mnemonic == "lload_1":
            self.gen_load_local(1, ir.i64)
        elif mnemonic == "lload_2":
            self.gen_load_local(2, ir.i64)
        elif mnemonic == "lload_3":
            self.gen_load_local(3, ir.i64)
        elif mnemonic == "fload_0":
            self.gen_load_local(0, ir.f32)
        elif mnemonic == "fload_1":
            self.gen_load_local(1, ir.f32)
        elif mnemonic == "fload_2":
            self.gen_load_local(2, ir.f32)
        elif mnemonic == "fload_3":
            self.gen_load_local(3, ir.f32)
        elif mnemonic == "dload_0":
            self.gen_load_local(0, ir.f64)
        elif mnemonic == "dload_1":
            self.gen_load_local(1, ir.f64)
        elif mnemonic == "dload_2":
            self.gen_load_local(2, ir.f64)
        elif mnemonic == "dload_3":
            self.gen_load_local(3, ir.f64)
        elif mnemonic == "istore":
            index = args[0]
            self.gen_store_local(index, ir.i32)
        elif mnemonic == "lstore":
            index = args[0]
            self.gen_store_local(index, ir.i64)
        elif mnemonic == "fstore":
            index = args[0]
            self.gen_store_local(index, ir.f32)
        elif mnemonic == "dstore":
            index = args[0]
            self.gen_store_local(index, ir.f64)
        elif mnemonic == "istore_0":
            self.gen_store_local(0, ir.i32)
        elif mnemonic == "istore_1":
            self.gen_store_local(1, ir.i32)
        elif mnemonic == "istore_2":
            self.gen_store_local(2, ir.i32)
        elif mnemonic == "istore_3":
            self.gen_store_local(3, ir.i32)
        elif mnemonic == "lstore_0":
            self.gen_store_local(0, ir.i64)
        elif mnemonic == "lstore_1":
            self.gen_store_local(1, ir.i64)
        elif mnemonic == "lstore_2":
            self.gen_store_local(2, ir.i64)
        elif mnemonic == "lstore_3":
            self.gen_store_local(3, ir.i64)
        elif mnemonic == "fstore_0":
            self.gen_store_local(0, ir.f32)
        elif mnemonic == "fstore_1":
            self.gen_store_local(1, ir.f32)
        elif mnemonic == "fstore_2":
            self.gen_store_local(2, ir.f32)
        elif mnemonic == "fstore_3":
            self.gen_store_local(3, ir.f32)
        elif mnemonic == "dstore_0":
            self.gen_store_local(0, ir.f64)
        elif mnemonic == "dstore_1":
            self.gen_store_local(1, ir.f64)
        elif mnemonic == "dstore_2":
            self.gen_store_local(2, ir.f64)
        elif mnemonic == "dstore_3":
            self.gen_store_local(3, ir.f64)
        elif mnemonic == "pop":
            value = self.stack.pop()
        elif mnemonic == "dup":
            value = self.stack.pop()
            self.stack.append(value)
            self.stack.append(value)
        elif mnemonic == "swap":
            value1 = self.stack.pop()
            value2 = self.stack.pop()
            self.stack.append(value1)
            self.stack.append(value2)
        elif mnemonic == "iadd":
            self.gen_binop("+", ir.i32)
        elif mnemonic == "ladd":
            self.gen_binop("+", ir.i64)
        elif mnemonic == "fadd":
            self.gen_binop("+", ir.f32)
        elif mnemonic == "dadd":
            self.gen_binop("+", ir.f64)
        elif mnemonic == "isub":
            self.gen_binop("-", ir.i32)
        elif mnemonic == "lsub":
            self.gen_binop("-", ir.i64)
        elif mnemonic == "fsub":
            self.gen_binop("-", ir.f32)
        elif mnemonic == "dsub":
            self.gen_binop("-", ir.f64)
        elif mnemonic == "imul":
            self.gen_binop("*", ir.i32)
        elif mnemonic == "lmul":
            self.gen_binop("*", ir.i64)
        elif mnemonic == "fmul":
            self.gen_binop("*", ir.f32)
        elif mnemonic == "dmul":
            self.gen_binop("*", ir.f64)
        elif mnemonic == "idiv":
            self.gen_binop("/", ir.i32)
        elif mnemonic == "ldiv":
            self.gen_binop("/", ir.i64)
        elif mnemonic == "fdiv":
            self.gen_binop("/", ir.f32)
        elif mnemonic == "ddiv":
            self.gen_binop("/", ir.f64)
        elif mnemonic == "i2l":
            self.gen_cast(ir.i32, ir.i64)
        elif mnemonic == "i2f":
            self.gen_cast(ir.i32, ir.f32)
        elif mnemonic == "i2d":
            self.gen_cast(ir.i32, ir.f64)
        elif mnemonic == "l2i":
            self.gen_cast(ir.i64, ir.i32)
        elif mnemonic == "l2f":
            self.gen_cast(ir.i64, ir.f32)
        elif mnemonic == "l2d":
            self.gen_cast(ir.i64, ir.f64)
        elif mnemonic == "f2i":
            self.gen_cast(ir.f32, ir.i32)
        elif mnemonic == "f2l":
            self.gen_cast(ir.f32, ir.i64)
        elif mnemonic == "f2d":
            self.gen_cast(ir.f32, ir.f64)
        elif mnemonic == "d2i":
            self.gen_cast(ir.f64, ir.i32)
        elif mnemonic == "d2l":
            self.gen_cast(ir.f64, ir.i64)
        elif mnemonic == "d2f":
            self.gen_cast(ir.f64, ir.f32)
        elif mnemonic == "i2b":
            self.gen_cast(ir.i32, ir.i8)
        elif mnemonic == "i2c":
            self.gen_cast(ir.i32, ir.i8)
        elif mnemonic == "i2s":
            self.gen_cast(ir.i32, ir.i16)
        elif mnemonic == "ireturn":
            self.gen_return(ir.i32)
        elif mnemonic == "lreturn":
            self.gen_return(ir.i64)
        elif mnemonic == "freturn":
            self.gen_return(ir.f32)
        elif mnemonic == "dreturn":
            self.gen_return(ir.f64)
        elif mnemonic == "return":
            self.emit(ir.Exit())
        elif mnemonic == "invokestatic":
            method_index = args[0]
            method_ref = self.class_file.constant_pool[method_index]
            # print(method_ref)
            # TODO: use --> class_index = method_ref.value[0]
            name_and_type_index = method_ref.value[1]
            name_and_type = self.class_file.constant_pool[name_and_type_index]
            # print(class_index, name_and_type)
            name = self.class_file.constant_pool[name_and_type.value[0]]
            signature = self.class_file.constant_pool[name_and_type.value[1]]
            logger.debug("calling %s with %s", name.value, signature.value)
            name = name.value
            signature = parse_method_descriptor(signature.value)
            self.call_sub(name, signature)
        else:  # pragma: no cover
            # logger.error('todo: 0x%X', instruction)
            raise NotImplementedError(mnemonic)

    def call_sub(self, name, signature):
        """ Call a function / method """
        ir_method = self.get_method_ref(name, signature)

        # Gather arguments from stack:
        args = []
        for parameter_type in signature.parameter_types:
            ir_typ = self.get_ir_type(parameter_type)
            arg = self.stack.pop()
            assert arg.ty is ir_typ
            args.append(arg)

        # Invoke tha method:
        is_void = isinstance(ir_method, ir.Procedure)
        if is_void:
            self.emit(ir.ProcedureCall(ir_method, args))
        else:
            typ = ir_method.return_ty
            value = self.emit(
                ir.FunctionCall(ir_method, args, "invokestatic", typ)
            )
            self.stack.append(value)

    def get_method_ref(self, name, signature):
        """ Retrieve a method with the given name and signature. """
        if name in self._functions:
            func = self._functions[name]
            # Check types?
        else:
            # Create new external method.
            raise NotImplementedError("TODO")
        return func

    def gen_load_const(self, value, typ):
        """ Generate code for loading a constant value. """
        value = self.emit(ir.Const(value, "const", typ))
        self.stack.append(value)

    def gen_load_local(self, index, typ):
        """ Generate code for loading a local variable. """
        var = self.local_variables[index]
        value = self.emit(ir.Load(var, "load", typ))
        assert value.ty == typ
        self.stack.append(value)

    def gen_store_local(self, index, typ):
        """ Generate code for storing a local variable. """
        value = self.stack.pop()
        assert value.ty == typ
        address = self.local_variables[index]
        print(address)
        self.emit(ir.Store(value, address))

    def gen_binop(self, op, typ):
        """ Generate code for a binary operation. """
        value1 = self.stack.pop()
        value2 = self.stack.pop()
        assert value1.ty is typ
        assert value2.ty is typ
        result = self.emit(ir.Binop(value1, op, value2, "binop", typ))
        self.stack.append(result)

    def gen_cast(self, from_typ, to_typ):
        """ Generate code for a type cast. """
        value = self.stack.pop()
        assert value.ty is from_typ
        result = self.emit(ir.Cast(value, "cast", to_typ))
        self.stack.append(result)

    def gen_return(self, typ):
        """ Generate code for a function return. """
        value = self.stack.pop()
        assert value.ty is typ
        self.emit(ir.Return(value))
