
""" Java virtual machine (JVM).

This module supports loading and saving of java bytecode.

See also:

https://en.wikipedia.org/wiki/Java_bytecode_instruction_listings
"""

# TODO: work in progress


opcodes = [
    ('nop', 0x00),
    ('aconst_null', 0x01),
    ('iconst_m1', 0x02),
    ('iconst_0', 0x03),
    ('iconst_1', 0x04),
    ('iconst_2', 0x05),
    ('iconst_3', 0x06),
    ('iconst_4', 0x07),
    ('iconst_5', 0x08),
    ('lconst_0', 0x09),
    ('lconst_1', 0x0a),
    ('fconst_0', 0x0b),
    ('fconst_1', 0x0c),
    ('fconst_2', 0x0d),
    ('dconst_0', 0x0e),
    ('dconst_1', 0x0f),
    ('bipush', 0x10),
    ('sipush', 0x11),
    ('ldc', 0x12),
    ('ldc_w', 0x13),
    ('ldc2_w', 0x14),
    ('iload', 0x15),
    ('lload', 0x16),
    ('fload', 0x17),
    ('dload', 0x18),
    ('aload', 0x19),
    ('iload_0', 0x1a),
    ('iload_1', 0x1b),
    ('iload_2', 0x1c),
    ('iload_3', 0x1d),
    # TODO: complete list?

]
