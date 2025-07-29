"""Create a nice christmas card."""

import sys
import os
import io
from ppci import api
from ppci.lang.basic.c64 import write_basic_program, BasicLine
from ppci.binutils.layout import Layout, Memory, Section
from ppci.utils.reporting import HtmlReportGenerator
import qrcode
from PIL import Image


# Mapping of 2x2 pixels to charcode:
# Value order:
# 0  1
# 2  3
charmap = {
    (0, 0, 0, 0): 32,
    (0, 0, 0, 1): 108,
    (0, 0, 1, 0): 123,
    (0, 0, 1, 1): 98,
    (0, 1, 0, 0): 124,
    (0, 1, 0, 1): 225,
    (0, 1, 1, 0): 255,
    (0, 1, 1, 1): 254,
    (1, 0, 0, 0): 126,
    (1, 0, 0, 1): 127,
    (1, 0, 1, 0): 97,
    (1, 0, 1, 1): 252,
    (1, 1, 0, 0): 226,
    (1, 1, 0, 1): 251,
    (1, 1, 1, 0): 236,
    (1, 1, 1, 1): 160,
}


def get_pix(qr_image, x, y):
    if y < qr_image.height and x < qr_image.width:
        v = qr_image.getpixel((x, y))
        if v == 0:
            return 0
        else:
            return 1
    else:
        return 1


def make_qr_data(text):
    qr_image = qrcode.make(
        text, box_size=1, border=0, error_correction=qrcode.ERROR_CORRECT_M
    )
    qr_pet = []
    print(qr_image.size)
    for y in range(25):
        for x in range(40):
            pattern = (
                get_pix(qr_image, x * 2, y * 2),
                get_pix(qr_image, x * 2 + 1, y * 2),
                get_pix(qr_image, x * 2, y * 2 + 1),
                get_pix(qr_image, x * 2 + 1, y * 2 + 1),
            )
            p = charmap[pattern]
            qr_pet.append(p)
    return bytes(qr_pet)


def make_sprite():
    im = Image.open("/home/windel/snowflake.png")
    assert im.size == (24, 21)
    sprite_data = []
    for y in range(21):
        for x in range(3):
            b = 0
            for x2 in range(8):
                v = im.getpixel((x * 8 + x2, y))
                b = (b << 1) | v
            sprite_data.append(b)
    return bytes(sprite_data)


march = api.get_arch("mcs6500")


class Sprite:
    pass


asm_src = """

    ; Display qr code:
    ; Use indirect-indexed mode here.
    lda #0x80
    sta 0xfb
    lda #0x20
    sta 0xfc
    lda #0x00
    sta 0xfd
    lda #0x04
    sta 0xfe

    ldx #0
qr_loop:
    ldy #0
qr_loop_inner:
    lda (0xfb),y
    sta (0xfd), y
    iny
    cpy #0x0
    bne qr_loop_inner
    inc 0xfc
    inc 0xfe
    inx
    cpx #3
    bne qr_loop

    ldy #0
qr_loop_last:
    lda (0xfb),y
    sta (0xfd), y
    iny
    cpy #232
    bne qr_loop_last

    ; Setup sprite pointer 1 to 0x80 * 0x40 = 0x2000
    lda #0x80
    sta 0x07f8
    sta 0x07f9
    sta 0x07fa
    sta 0x07fb

    sta 0x07fc
    sta 0x07fd
    sta 0x07fe
    sta 0x07ff

    ; Enable sprite 1:
    lda #0xff
    sta  0xd015

    ; X and Y coordinate:
    lda # 32
    sta 0xd000 ; x coordinate
    sta 0xd001 ; y coordinate

    lda # 0x40
    sta 0xd002 ; x coordinate
    lda # 200
    sta 0xd003 ; y coordinate

    lda # 96 ; pos = 64,64
    sta 0xd004 ; x coordinate
    sta 0xd005 ; y coordinate

    lda # 150
    sta 0xd006 ; x coordinate
    lda # 150
    sta 0xd007 ; y coordinate

    lda # 170
    sta 0xd008 ; x coordinate
    lda # 10
    sta 0xd009 ; y coordinate

    lda # 180
    sta 0xd00a ; x coordinate
    lda # 10
    sta 0xd00b ; y coordinate

    lda # 210
    sta 0xd00c ; x coordinate
    lda # 200
    sta 0xd00d ; y coordinate

    lda # 255
    sta 0xd00e ; x coordinate
    lda # 80
    sta 0xd00f ; y coordinate

    lda #0
    sta 0xfb

loop:

    ; wait for vertical retrace:
    lda #251
loop2:
    cmp 0xd012
    bne loop2

    inc 0xfb
    lda 0xfb
    cmp #5
    bne loop

    lda #0
    sta 0xfb

    ; Action:
    jsr update

    jmp loop
    rts

update:
    ; inc 0xd000

    inc 0xd001
    inc 0xd003
    inc 0xd005
    inc 0xd007

    inc 0xd009
    inc 0xd00b
    inc 0xd00d
    inc 0xd00f
    rts
"""

# sprite = bytes(range(63))
sprite = make_sprite()
print(sprite)

f = io.StringIO(asm_src)
oj = api.asm(f, march)
print(oj)

layout = Layout()
ram = Memory("ram")
ram.location = 0x890
ram.size = 0x1000
ram.add_input(Section("code"))
layout.add_memory(ram)

oj = api.link([oj], layout=layout)

asm_bin = oj.get_image("ram").data
print(oj, asm_bin)

if len(sys.argv) > 1:
    message = sys.argv[1]
else:
    message = "You can provide a message via an argument"


with open("c64disk/card.prg", "wb") as f:
    load_address = 0x801
    sys_address = 0x890
    sprite_address = 0x2000
    qr_address = 0x2080
    address_text = str(sys_address).encode("ascii")
    program = []
    program.append(BasicLine(1000, bytes([0x9E]) + address_text))
    write_basic_program(program, f)
    pos = f.tell() - 2
    max_basic_size = sys_address - load_address
    if pos < max_basic_size:
        f.seek(sys_address - load_address + 2)
        print(pos)
        f.write(asm_bin)
        f.seek(sprite_address - load_address + 2)
        f.write(sprite)
        f.seek(qr_address - load_address + 2)
        qr_data = make_qr_data(message)
        f.write(qr_data)
