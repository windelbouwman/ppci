""" Caml opcodes.

See also: http://cadmium.x9c.fr/distrib/caml-instructions.pdf

"""

opcodes = (
    (0, "ACC0"),
    (1, "ACC1"),
    (2, "ACC2"),
    (3, "ACC3"),
    (4, "ACC4"),
    (5, "ACC5"),
    (6, "ACC6"),
    (7, "ACC7"),
    (8, "ACC", ("n",)),
    (9, "PUSH"),
    (10, "PUSHACC0"),
    (11, "PUSHACC1"),
    (12, "PUSHACC2"),
    (13, "PUSHACC3"),
    (14, "PUSHACC4"),
    (15, "PUSHACC5"),
    (16, "PUSHACC6"),
    (17, "PUSHACC7"),
    (18, "PUSHACC", ("n",)),
    (19, "POP", ("n",)),
    (20, "ASSIGN", ("n",)),
    (21, "ENVACC1"),
    (22, "ENVACC2"),
    (23, "ENVACC3"),
    (24, "ENVACC4"),
    (25, "ENVACC", ("n",)),
    (26, "PUSHENVACC1"),
    (27, "PUSHENVACC2"),
    (28, "PUSHENVACC3"),
    (29, "PUSHENVACC4"),
    (30, "PUSHENVACC", ("n",)),
    (31, "PUSH-RETADDR", ("ofs",)),
    (32, "APPLY", ("args",)),
    (33, "APPLY1"),
    (34, "APPLY2"),
    (35, "APPLY3"),
    (36, "APPTERM", ("n", "s")),
    (37, "APPTERM1", ("n",)),
    (38, "APPTERM2", ("n",)),
    (39, "APPTERM3", ("n",)),
    (40, "RETURN", ("n",)),
    (41, "RESTART"),
    (42, "GRAB", ("n",)),
    (43, "CLOSURE", ("n", "ofs")),
    (44, "CLOSUREREC", ("f", "v", "o", "t")),
    (45, "OFFSETCLOSUREM2"),
    (46, "OFFSETCLOSURE0"),
    (47, "OFFSETCLOSURE2"),
    (48, "OFFSETCLOSURE", ("n",)),
    (49, "PUSHOFFSETCLOSUREM2"),
    (50, "PUSHOFFSETCLOSURE0"),
    (51, "PUSHOFFSETCLOSURE2"),
    (52, "PUSHOFFSETCLOSURE", ("n",)),
    (53, "GETGLOBAL", ("n",)),
    (54, "PUSHGETGLOBAL", ("n",)),
    (55, "GETGLOBALFIELD", ("n", "p")),
    (56, "PUSHGETGLOBALFIELD", ("n", "p")),
    (57, "SETGLOBAL", ("n",)),
    (58, "ATOM0"),
    (59, "ATOM", ("n",)),
    (60, "PUSHATOM0"),
    (61, "PUSHATOM", ("n",)),
    (62, "MAKEBLOCK", ("n", "t")),
    (63, "MAKEBLOCK1", ("t",)),
    (64, "MAKEBLOCK2", ("t",)),
    (65, "MAKEBLOCK3", ("t",)),
    (66, "MAKEFLOATBLOCK", ("n",)),
    (67, "GETFIELD0"),
    (68, "GETFIELD1"),
    (69, "GETFIELD2"),
    (70, "GETFIELD3"),
    (71, "GETFIELD", ("n",)),
    (72, "GETFLOATFIELD", ("n",)),
    (73, "SETFIELD0"),
    (74, "SETFIELD1"),
    (75, "SETFIELD2"),
    (76, "SETFIELD3"),
    (77, "SETFIELD", ("n",)),
    (78, "SETFLOATFIELD", ("n",)),
    (79, "VECTLENGTH"),
    (80, "GETVECTITEM"),
    (81, "SETVECTITEM"),
    (82, "GETSTRINGCHAR"),
    (83, "SETSTRINGCHAR"),
    (84, "BRANCH", ("ofs",)),
    (85, "BRANCHIF", ("ofs",)),
    (86, "BRANCHIFNOT", ("ofs",)),
    (87, "SWITCH", ("n", "tab")),
    (88, "BOOLNOT"),
    (89, "PUSHTRAP", ("ofs",)),
    (90, "POPTRAP"),
    (91, "RAISE"),
    (92, "CHECK-SIGNALS"),
    (93, "C-CALL1", ("p",)),
    (94, "C-CALL2", ("p",)),
    (95, "C-CALL3", ("p",)),
    (96, "C-CALL4", ("p",)),
    (97, "C-CALL5", ("p",)),
    (98, "C-CALLN", ("n", "p")),
    (99, "CONST0"),
    (100, "CONST1"),
    (101, "CONST2"),
    (102, "CONST3"),
    (103, "CONSTINT", ("n",)),
    (104, "PUSHCONST0"),
    (105, "PUSHCONST1"),
    (106, "PUSHCONST2"),
    (107, "PUSHCONST3"),
    (108, "PUSHCONSTINT", ("n",)),
    (109, "NEGINT"),
    (110, "ADDINT"),
    (111, "SUBINT"),
    (112, "MULINT"),
    (113, "DIVINT"),
    (114, "MODINT"),
    (115, "ANDINT"),
    (116, "ORINT"),
    (117, "XORINT"),
    (118, "LSLINT"),
    (119, "LSRINT"),
    (120, "ASRINT"),
    (121, "EQ"),
    (122, "NEQ"),
    (123, "LTINT"),
    (124, "LEINT"),
    (125, "GTINT"),
    (126, "GEINT"),
    (127, "OFFSETINT", ("ofs",)),
    (128, "OFFSETREF", ("ofs",)),
    (129, "ISINT"),
    (130, "GETMETHOD"),
    (131, "BEQ", ("val", "ofs")),
    (132, "BNEQ", ("val", "ofs")),
    (133, "BLTINT", ("val", "ofs")),
    (134, "BLEINT", ("val", "ofs")),
    (135, "BGTINT", ("val", "ofs")),
    (136, "BGEINT", ("val", "ofs")),
    (137, "ULTINT"),
    (138, "UGEINT"),
    (139, "BULTINT", ("val", "ofs")),
    (140, "BUGEINT", ("val", "ofs")),
    (141, "GETPUBMET", ("tag", "cache")),
    (142, "GETDYNMET"),
    (143, "STOP"),
    (144, "EVENT"),
    (145, "BREAK"),
    (146, "RERAISE"),
    (147, "RAISE_NOTRACE"),
)


def process_opcode_table():
    assert len(opcodes) == 148

    mp = {}
    attrs = {}

    for opcode in opcodes:
        # print(opcode)
        code = opcode[0]
        name = opcode[1]
        assert isinstance(code, int)
        assert isinstance(name, str)
        assert code not in mp
        if len(opcode) > 2:
            args = opcode[2]
        else:
            args = tuple()
        assert isinstance(args, tuple)
        mp[code] = name, args
        attrs[name] = code
    opcode = type("Opcode", (object,), attrs)()
    return mp, opcode


Instrs, Opcode = process_opcode_table()


class Instruction:
    def __init__(self, opcode, name, args):
        # if opcode not in Instrs:
        #    raise ValueError('Invalid opcode {}'.format(opcode))

        self.opcode = opcode
        self.name = name
        self.args = args

    def __str__(self):
        return "{} {}".format(self.name, self.args)
