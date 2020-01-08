""" Small helper to convert binary data into text and vice-versa.
"""
import binascii
from .chunk import chunks


def bin2asc(data: bytes):
    """ Encode binary data as ascii. If it is a large data set, then use a
        list of hex characters.
    """
    if len(data) > 30:
        res = []
        for part in chunks(data):
            res.append(binascii.hexlify(part).decode("ascii"))
        return res
    else:
        return binascii.hexlify(data).decode("ascii")


def asc2bin(data) -> bytes:
    """ Decode ascii into binary """
    if isinstance(data, str):
        return bytes(binascii.unhexlify(data.encode("ascii")))
    elif isinstance(data, list):
        res = bytearray()
        for part in data:
            res.extend(binascii.unhexlify(part.encode("ascii")))
        return bytes(res)
    else:  # pragma: no cover
        raise NotImplementedError(str(type(data)))
