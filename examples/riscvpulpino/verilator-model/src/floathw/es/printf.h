/*************************************************************************
es-printf  -  configurable printf for embedded systems

printf.h: Header for consumers of printf functions.

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

#ifndef PRINTF_H
#define PRINTF_H

/*************************************************************************
Basic printf only

The code is designed to support a variety of printf-related functions.
If simple serial output is all you want then you can save some space by
defining BASIC_PRINTF_ONLY which allows the internal API to be simplified.
*************************************************************************/

//#define BASIC_PRINTF_ONLY

/*************************************************************************
Number of chars output

Traditionally printf returns the number of chars output. If you are not
interested in that value you can leave PRINTF_T undefined.
On a small micro you can define the return type as unsigned char if you
are sure the total output width will never exceed 255, or unsigned short.
*************************************************************************/

#define PRINTF_T unsigned short

// Create a type definition for the return value
#ifndef PRINTF_T
typedef void printf_t;
#else
typedef PRINTF_T printf_t;
#endif

/*************************************************************************
Memory access definitions

Some micros such as the AVR can only support storing strings in flash
memory by wrapping the string in a macro. To make this transparent we can
define the printf function itself as a macro which performs the wrap and
calls a renamed version of printf with a _rom suffix.
*************************************************************************/

/* Example for AVR micros using WinAVR (GCC) compiler

#define sprintf(buf, format, args...)   sprintf_rom(buf, PSTR(format), ## args)
#define printf(format, args...)         printf_rom(PSTR(format), ## args)

extern printf_t sprintf_rom(char *, const char *, ...);
extern printf_t printf_rom(const char *, ...);
*/

/*************************************************************************
Standard declarations

These are the declarations for the standard functions, unless overridden
by the memory access macros above.
*************************************************************************/

#ifndef printf
extern printf_t printf(const char *, ...);
#endif

#ifndef sprintf
extern printf_t sprintf(char *, const char *, ...);
#endif

#endif
