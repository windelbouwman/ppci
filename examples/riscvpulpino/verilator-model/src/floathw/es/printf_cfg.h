/*************************************************************************
es-printf  -  configurable printf for embedded systems

print_cfg.h: Select the build options for printf functions.

**************************************************************************
Copyright (c) 2006 - 2013 Skirrid Systems

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
******************************************************************************/

#ifndef PRINTF_CFG_H
#define PRINTF_CFG_H

/*************************************************************************
Memory access definitions

Some micros such as the AVR can only support storing and accessing strings
in flash memory using special macros and functions. This section can be
used to specify those methods. You may also need to modify printf.h
to get the compiler to place the format strings in flash memory.

The GET_FORMAT(ptr) macro is used to access a character in the printf
format string. By default this does a normal memory pointer access, but
you can configure it to access flash memory if needed.
*************************************************************************/

/* Example for AVR micros using WinAVR (GCC) compiler

#include <avr/io.h>
#include <avr/pgmspace.h>
#define GET_FORMAT(p)   pgm_read_byte(p)
*/

/*************************************************************************
Output configuration

By default printf will use the putchar function. If this is not defined
in your system you can set your own function here by defining
PUTCHAR_FUNC to be the name of that function.
*************************************************************************/

/*
extern void putc(char c);
#define PUTCHAR_FUNC    putc
*/

/*************************************************************************
Compiler capability configuration

Set some options that the C pre-processor will not tell us about.
*************************************************************************/

// Does the compiler support double precision or silently degrade to single?
#define NO_DOUBLE_PRECISION

/*************************************************************************
Formatted item width

Since it is extremely unlikely that you will ever want to use a formatted
width for a single item of more than 127 chars (i.e. the expanded and
padded size of a single % expression), the width variables can normally
be restricted to 8 bits. On small micros this saves a lot of code and
variable space. On a 32-bit RISC it may increase code size due to type
conversions. Choose the variable type to suit your CPU.
Note that a signed type is required.
*************************************************************************/

typedef signed char width_t;

/*************************************************************************
Feature configuration

This section defines the various feature flags.
These are combined as needed to produce the FEATURE_FLAGS macro.
*************************************************************************/

// Include floating point number support
#define USE_FLOAT       (1<<0)

// Include support for long integers
#define USE_LONG        (1<<1)

// Include support for octal formatting
#define USE_OCTAL       (1<<2)

// Include support for the %i synonym for %d
#define USE_SIGNED_I    (1<<3)

// Include support for the %u unsigned decimal specifier
#define USE_UNSIGNED    (1<<4)

// Include support for the %x hex specifier (lowercase output)
#define USE_HEX_LOWER   (1<<5)

// Include support for the %X hex specifier (uppercase output)
#define USE_HEX_UPPER   (1<<6)

// Force uppercase output with %x.
// Used in conjunction with USE_HEX_LOWER.
// Ignored if USE_HEX_UPPER is also set.
#define USE_HEX_UPPER_L (1<<7)

// Include precision support when floating point is not present.
// Precision is automatically enabled when floating point support is used.
#define USE_PRECISION   (1<<8)

// Allow use of leading zero padding e.g. "%03d"
#define USE_ZERO_PAD    (1<<9)

// Allow use of space padding e.g. "%3d" or "%12s"
#define USE_SPACE_PAD   (1<<10)

// Include indirect width/precision support e.g. "%*d"
#define USE_INDIRECT    (1<<11)

// Allow forcing a leading plus sign e.g. "%+3d"
#define USE_PLUS_SIGN   (1<<12)

// Allow forcing a leading space (instead of + or -) in front of zero e.g. "% 3d"
#define USE_SPACE_SIGN  (1<<13)

// Include support for the left-justify '-' flag.
#define USE_LEFT_JUST   (1<<14)

// Include support for the special '#' flag.
#define USE_SPECIAL     (1<<15)

/*************************************************************************
Pre-defined feature sets

This section provides some commonly used combinations of features.
*************************************************************************/

// Decimal and lowercase hex only.
#define MINIMAL_INT ( \
        USE_HEX_LOWER )

// Signed and unsigned decimal, lower case hex, zero & space padding.
#define BASIC_INT ( \
        USE_UNSIGNED | USE_HEX_LOWER | USE_ZERO_PAD | USE_SPACE_PAD )

// All short integer features except octal, %i, indirection and specials.
#define SHORT_INT ( \
        USE_UNSIGNED | USE_HEX_LOWER | USE_HEX_UPPER | \
        USE_PRECISION  | USE_ZERO_PAD   | USE_SPACE_PAD | \
        USE_PLUS_SIGN  | USE_SPACE_SIGN | USE_LEFT_JUST )

// As above, but also supports long integers.
#define LONG_INT ( \
        USE_LONG | SHORT_INT )

// All possible integer features.
#define FULL_INT ( \
        USE_OCTAL | USE_SIGNED_I | USE_INDIRECT | USE_SPECIAL | LONG_INT )

// All available features including floating point.
#define FULL_FLOAT ( \
        USE_FLOAT | FULL_INT )

// Custom feature set. Comment out features you don't want.
#define CUSTOM_SET ( \
        USE_FLOAT       \
        USE_LONG        \
        USE_OCTAL       \
        USE_SIGNED_I    \
        USE_UNSIGNED    \
        USE_HEX_LOWER   \
        USE_HEX_UPPER   \
        USE_HEX_UPPER_L \
        USE_PRECISION   \
        USE_ZERO_PAD    \
        USE_SPACE_PAD   \
        USE_INDIRECT    \
        USE_PLUS_SIGN   \
        USE_SPACE_SIGN  \
        USE_LEFT_JUST   \
        USE_SPECIAL     \
)

// Current feature set. Use a pre-defined set or define your own.
#define FEATURE_FLAGS   FULL_FLOAT

#endif
