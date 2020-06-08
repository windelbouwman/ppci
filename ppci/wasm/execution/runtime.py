""" Wasm runtime functions.

"""

import struct
import math
from ... import ir
from ...utils.bitfun import rotr, rotl, to_signed, to_unsigned
from ...utils.bitfun import clz, ctz, popcnt, sign_extend
from ..util import make_int


class Unreachable(RuntimeError):
    """ WASM kernel panic. Having an exception for this allows catching it
    in tests.
    """

    pass


def f32_sqrt(v: ir.f32) -> ir.f32:
    """ Square root """
    return math.sqrt(v)


def f64_sqrt(v: ir.f64) -> ir.f64:
    return math.sqrt(v)


def i32_rotr(v: ir.i32, cnt: ir.i32) -> ir.i32:
    """ Rotate right """
    return to_signed(rotr(to_unsigned(v, 32), cnt, 32), 32)


def i64_rotr(v: ir.i64, cnt: ir.i64) -> ir.i64:
    """ Rotate right """
    return to_signed(rotr(to_unsigned(v, 64), cnt, 64), 64)


def i32_rotl(v: ir.i32, cnt: ir.i32) -> ir.i32:
    """ Rotate left """
    return to_signed(rotl(to_unsigned(v, 32), cnt, 32), 32)


def i64_rotl(v: ir.i64, cnt: ir.i64) -> ir.i64:
    """ Rotate left """
    return to_signed(rotl(to_unsigned(v, 64), cnt, 64), 64)


# Bit counting:
def i32_clz(v: ir.i32) -> ir.i32:
    return clz(v, 32)


def i64_clz(v: ir.i64) -> ir.i64:
    return clz(v, 64)


def i32_ctz(v: ir.i32) -> ir.i32:
    return ctz(v, 32)


def i64_ctz(v: ir.i64) -> ir.i64:
    return ctz(v, 64)


def i32_popcnt(v: ir.i32) -> ir.i32:
    return popcnt(v, 32)


def i64_popcnt(v: ir.i64) -> ir.i64:
    return popcnt(v, 64)


# Conversions:
def i32_trunc_f32_s(value: ir.f32) -> ir.i32:
    if math.isinf(value):
        return 0  # undefined
    else:
        return int(value)


def i32_trunc_f32_u(value: ir.f32) -> ir.i32:
    if math.isinf(value):
        return 0  # undefined
    else:
        return make_int(value, 32)


def i32_trunc_f64_s(value: ir.f64) -> ir.i32:
    if math.isinf(value):
        return 0  # undefined
    else:
        return int(value)


def i32_trunc_f64_u(value: ir.f64) -> ir.i32:
    if math.isinf(value):
        return 0  # undefined
    else:
        return make_int(value, 32)


def i64_trunc_f32_s(value: ir.f32) -> ir.i64:
    if math.isinf(value):
        return 0  # undefined
    else:
        return int(value)


def i64_trunc_f32_u(value: ir.f32) -> ir.i64:
    if math.isinf(value):
        return 0  # undefined
    else:
        return make_int(value, 64)


def i64_trunc_f64_s(value: ir.f64) -> ir.i64:
    if math.isinf(value):
        return 0  # undefined
    else:
        return int(value)


def i64_trunc_f64_u(value: ir.f64) -> ir.i64:
    if math.isinf(value):
        return 0  # undefined
    else:
        return make_int(value, 64)


# saturated trunc


def satured_truncate(value: float, lower_limit, upper_limit) -> int:
    if math.isinf(value):
        if value > 0:
            return upper_limit
        else:
            return lower_limit
    if value > upper_limit:
        return upper_limit
    elif value < lower_limit:
        return lower_limit
    else:
        return int(value)


MAX_I32 = 2 ** 31 - 1
MIN_I32 = -(2 ** 31)
MAX_U32 = 2 ** 32 - 1
MIN_U32 = 0


def i32_trunc_sat_f32_s(v: ir.f32) -> ir.i32:
    return satured_truncate(v, MIN_I32, MAX_I32)


def i32_trunc_sat_f32_u(v: ir.f32) -> ir.i32:
    return make_int(satured_truncate(v, MIN_U32, MAX_U32), 32)


def i32_trunc_sat_f64_s(v: ir.f64) -> ir.i32:
    return satured_truncate(v, MIN_I32, MAX_I32)


def i32_trunc_sat_f64_u(v: ir.f64) -> ir.i32:
    return make_int(satured_truncate(v, MIN_U32, MAX_U32), 32)


MAX_I64 = 2 ** 63 - 1
MIN_I64 = -(2 ** 63)
MAX_U64 = 2 ** 64 - 1
MIN_U64 = 0


def i64_trunc_sat_f32_s(v: ir.f32) -> ir.i64:
    return satured_truncate(v, MIN_I64, MAX_I64)


def i64_trunc_sat_f32_u(v: ir.f32) -> ir.i64:
    return make_int(satured_truncate(v, MIN_U64, MAX_U64), 64)


def i64_trunc_sat_f64_s(v: ir.f64) -> ir.i64:
    return satured_truncate(v, MIN_I64, MAX_I64)


def i64_trunc_sat_f64_u(v: ir.f64) -> ir.i64:
    return make_int(satured_truncate(v, MIN_U64, MAX_U64), 64)


# Promote / demote


def f64_promote_f32(v: ir.f32) -> ir.f64:
    return v


def f32_demote_f64(v: ir.f64) -> ir.f32:
    return v


def f64_reinterpret_i64(v: ir.i64) -> ir.f64:
    x = struct.pack("<q", v)
    return struct.unpack("<d", x)[0]


def i64_reinterpret_f64(v: ir.f64) -> ir.i64:
    x = struct.pack("<d", v)
    return struct.unpack("<q", x)[0]


def f32_reinterpret_i32(v: ir.i32) -> ir.f32:
    x = struct.pack("<i", v)
    return struct.unpack("<f", x)[0]


def i32_reinterpret_f32(v: ir.f32) -> ir.i32:
    x = struct.pack("<f", v)
    return struct.unpack("<i", x)[0]


def f32_copysign(x: ir.f32, y: ir.f32) -> ir.f32:
    return math.copysign(x, y)


def f64_copysign(x: ir.f64, y: ir.f64) -> ir.f64:
    return math.copysign(x, y)


def f32_min(x: ir.f32, y: ir.f32) -> ir.f32:
    return min(x, y)


def f64_min(x: ir.f64, y: ir.f64) -> ir.f64:
    return min(x, y)


def f32_max(x: ir.f32, y: ir.f32) -> ir.f32:
    return max(x, y)


def f64_max(x: ir.f64, y: ir.f64) -> ir.f64:
    return max(x, y)


def f32_abs(x: ir.f32) -> ir.f32:
    return math.fabs(x)


def f64_abs(x: ir.f64) -> ir.f64:
    return math.fabs(x)


def f32_floor(x: ir.f32) -> ir.f32:
    if math.isinf(x):
        return x
    else:
        return float(math.floor(x))


def f64_floor(x: ir.f64) -> ir.f64:
    if math.isinf(x):
        return x
    else:
        return float(math.floor(x))


def f32_ceil(x: ir.f32) -> ir.f32:
    if math.isinf(x):
        return x
    else:
        return float(math.ceil(x))


def f64_ceil(x: ir.f64) -> ir.f64:
    if math.isinf(x):
        return x
    else:
        return float(math.ceil(x))


def f32_nearest(x: ir.f32) -> ir.f32:
    if math.isinf(x):
        return x
    else:
        return float(round(x))


def f64_nearest(x: ir.f64) -> ir.f64:
    if math.isinf(x):
        return x
    else:
        return float(round(x))


def f32_trunc(x: ir.f32) -> ir.f32:
    if math.isinf(x):
        return x
    else:
        return float(math.trunc(x))


def f64_trunc(x: ir.f64) -> ir.f64:
    if math.isinf(x):
        return x
    else:
        return float(math.trunc(x))


def unreachable() -> None:
    raise Unreachable("WASM KERNEL panic!")


def i32_extend8_s(x: ir.i32) -> ir.i32:
    return sign_extend(x, 8)


def i32_extend16_s(x: ir.i32) -> ir.i32:
    return sign_extend(x, 16)


def i64_extend8_s(x: ir.i64) -> ir.i64:
    return sign_extend(x, 8)


def i64_extend16_s(x: ir.i64) -> ir.i64:
    return sign_extend(x, 16)


def i64_extend32_s(x: ir.i64) -> ir.i64:
    return sign_extend(x, 32)


# See also:
# https://github.com/kanaka/warpy/blob/master/warpy.py
def create_runtime():
    """ Create runtime functions.

    These are functions required by some wasm instructions which cannot
    be code generated directly or are too complex.
    """

    runtime = {
        "f32_sqrt": f32_sqrt,
        "f64_sqrt": f64_sqrt,
        "i32_rotl": i32_rotl,
        "i64_rotl": i64_rotl,
        "i32_rotr": i32_rotr,
        "i64_rotr": i64_rotr,
        "i32_clz": i32_clz,
        "i64_clz": i64_clz,
        "i32_ctz": i32_ctz,
        "i64_ctz": i64_ctz,
        "i32_popcnt": i32_popcnt,
        "i64_popcnt": i64_popcnt,
        "i32_trunc_f32_s": i32_trunc_f32_s,
        "i32_trunc_f32_u": i32_trunc_f32_u,
        "i32_trunc_f64_s": i32_trunc_f64_s,
        "i32_trunc_f64_u": i32_trunc_f64_u,
        "i64_trunc_f32_s": i64_trunc_f32_s,
        "i64_trunc_f32_u": i64_trunc_f32_u,
        "i64_trunc_f64_s": i64_trunc_f64_s,
        "i64_trunc_f64_u": i64_trunc_f64_u,
        "f64_promote_f32": f64_promote_f32,
        "f32_demote_f64": f32_demote_f64,
        "f64_reinterpret_i64": f64_reinterpret_i64,
        "i64_reinterpret_f64": i64_reinterpret_f64,
        "f32_reinterpret_i32": f32_reinterpret_i32,
        "i32_reinterpret_f32": i32_reinterpret_f32,
        "f32_copysign": f32_copysign,
        "f64_copysign": f64_copysign,
        "f32_min": f32_min,
        "f32_max": f32_max,
        "f64_min": f64_min,
        "f64_max": f64_max,
        "f32_abs": f32_abs,
        "f64_abs": f64_abs,
        "f32_floor": f32_floor,
        "f64_floor": f64_floor,
        "f32_nearest": f32_nearest,
        "f64_nearest": f64_nearest,
        "f32_ceil": f32_ceil,
        "f64_ceil": f64_ceil,
        "f32_trunc": f32_trunc,
        "f64_trunc": f64_trunc,
        "unreachable": unreachable,
        "i32_extend8_s": i32_extend8_s,
        "i32_extend16_s": i32_extend16_s,
        "i64_extend8_s": i64_extend8_s,
        "i64_extend16_s": i64_extend16_s,
        "i64_extend32_s": i64_extend32_s,
        "i32_trunc_sat_f32_s": i32_trunc_sat_f32_s,
        "i32_trunc_sat_f32_u": i32_trunc_sat_f32_u,
        "i32_trunc_sat_f64_s": i32_trunc_sat_f64_s,
        "i32_trunc_sat_f64_u": i32_trunc_sat_f64_u,
        "i64_trunc_sat_f32_s": i64_trunc_sat_f32_s,
        "i64_trunc_sat_f32_u": i64_trunc_sat_f32_u,
        "i64_trunc_sat_f64_s": i64_trunc_sat_f64_s,
        "i64_trunc_sat_f64_u": i64_trunc_sat_f64_u,
    }

    return runtime
