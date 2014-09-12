

def rotate_right(v, n):
    """ bit-wise Rotate right n times """
    mask = (2**n) - 1
    mask_bits = v & mask
    return (v >> n) | (mask_bits << (32 - n))

def rotate_left(v, n):
    assert n >= 0
    assert n < 32
    return rotate_right(v, 32 - n)

def encode_imm32(v):
    """ Bundle 32 bit value into 4 bits rotation and 8 bits value
     """
    for i in range(0, 16):
        v2 = rotate_left(v, i*2)
        if (v2 & 0xFFFFFF00) == 0:
            rotation = i
            val = v2 & 0xFF
            x = (rotation << 8) | val
            return x
    raise ValueError("Invalid value {}".format(v))

