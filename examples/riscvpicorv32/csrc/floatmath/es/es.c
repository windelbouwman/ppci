/*************************************************************************
es-printf  -  configurable printf for embedded systems

printf.c: Main source file for printf family of functions.

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

// System and config header files are included by the parent stub file.
#include <stdarg.h>
void bsp_putc(char);
void printfdbg(char* txt, ...);
 
//#include <string.h>
int strlen(const char *s)
{
    int count;

	count = 0;
	while (*s++ != '\0')
		count++;
	return(count);
} 

//#include <math.h>
#include "printf.h"
#include "printf_cfg.h"

/* Define default macro to access the format string using a pointer. */
#ifndef GET_FORMAT
    #define GET_FORMAT(p)   (*(p))
#endif

/* Define default function for printf output. */
#ifndef PUTCHAR_FUNC
    #define PUTCHAR_FUNC    bsp_putc
#endif

/* Renames the functions if they have been defined as macros in printf.h */
#ifdef printf
    #undef  printf
    #define printf printf_rom
#endif

#ifdef sprintf
    #undef  sprintf
    #define sprintf sprintf_rom
#endif

// Macro used to check presence of a feature flag.
// These are defined in print_cfg.h
#define FEATURE(flag)   (FEATURE_FLAGS & (flag))

// Size of buffer for formatting numbers into
#if FEATURE(USE_FLOAT)
    #define BUFMAX  30
#else
    #define BUFMAX  16
#endif

// Precision is required for floating point support
#if FEATURE(USE_FLOAT) && !FEATURE(USE_PRECISION)
    #undef FEATURE(USE_PRECISION)
    #define FEATURE(USE_PRECISION)   1
#endif

// Bits in the flags variable
#if FEATURE(USE_LEFT_JUST)
#define FL_LEFT_JUST    (1<<0)
#else
#define FL_LEFT_JUST    0
#endif
#define FL_ZERO_PAD     (1<<1)
#define FL_SPECIAL      (1<<2)
#define FL_PLUS         (1<<3)
#define FL_SPACE        (1<<4)
#define FL_NEG          (1<<5)
#define FL_LONG         (1<<6)

// Bits in the fflags variable
#define FF_UCASE        (1<<0)
#define FF_FCVT         (1<<1)
#define FF_GCVT         (1<<2)

// Most compilers can support double precision
#ifndef NO_DOUBLE_PRECISION
  #define MAX_POWER     256
  #define FLOAT_DIGITS  17
#else
  #define MAX_POWER     32
  #define FLOAT_DIGITS  8
#endif

#if FEATURE(USE_FLOAT)
static const double smalltable[] = {
#ifndef NO_DOUBLE_PRECISION
    1e-256, 1e-128, 1e-64,
#endif
  1.0e-32, 1.0e-16, 1.0e-8, 1.0e-4, 1.0e-2, 1.0e-1, 1.0  
  //0.0001, 0.01, 0.1, 1.0
};
static const double largetable[] = {
#ifndef NO_DOUBLE_PRECISION
    1e+256, 1e+128, 1e+64,
#endif
    1.0e+32, 1.0e+16, 1.0e+8, 1.0e+4, 1.0e+2, 1.0e+1
};

// Function to trim trailing zeros and DP in 'g' mode.
// Return pointer to new string terminator position.
static char *trim_zeros(char *p)
{
    // Trim trailing 0's in 'g' mode.
    while (*p == '0')
        p--;
    // If last non-zero is DP, trim that as well.
    if (*p != '.') ++p;
    return p;
}

static char *format_float(double number, int ndigits, unsigned char flags, unsigned char fflags, char *buf)
{
    int decpt;
    int power10;
    unsigned char i;
    char *p = buf + 2;
    char *pend;
    
    // Handle special values
    /*if (isinf(number))
    {
        buf[0] = 'I';
        buf[1] = 'n';
        buf[2] = 'f';
        buf[3] = '\0';
        return buf;
    }
    if (isnan(number))
    {
        buf[0] = 'N';
        buf[1] = 'a';
        buf[2] = 'N';
        buf[3] = '\0';
        return buf;
    }*/

    // Handle all numbers as positive.
    if (number < 0)
    {
        number = -number;
        flags |= FL_NEG;
    }

    // Digits printed cannot be negative.
    if (ndigits < 0)
        ndigits = 0;

    // Prefill buffer with zeros.
    for (i = 0; i < BUFMAX; i++)
        buf[i] = '0';

    if (number == 0)
    {
        // Special case to correct number of decimals, significant figures,
        // and avoid printing 0E-00.
        ndigits++;
        decpt = 1;
    }
    else
    {
        /* Normalise the number such that it lies in the range 1 <= n < 10.
         * This is done using a binary search, making the largest possible
         * adjustment first and getting progressively smaller. This gets
         * to the answer in the fastest time, with the minimum number of
         * operations to introduce rounding errors.
         */
        decpt = 1;
        // First make small numbers bigger.
        power10 = MAX_POWER;
        i = 0;
        while (number < 1.0)
        {
            while (number < smalltable[i + 1])
            {
                number /= smalltable[i];
                decpt -= power10;
            }
            power10 >>= 1;
            i++;
        }
        
        // Then make big numbers smaller.
        power10 = MAX_POWER;
        i = 0;
        while (number >= 10.0)
        {
            while (number >= largetable[i])
            {
                number /= largetable[i];
                decpt += power10;
                // Avoid this loop hanging on infinity.
                if (decpt > 1000)
                {
                    buf[0] = 'I';
                    buf[1] = 'n';
                    buf[2] = 'f';
                    buf[3] = '\0';
                    return buf;
                }
            }
            power10 >>= 1;
            i++;
        }
        
    }
    
    // For g conversions determine whether to use e or f mode.
    if (fflags & FF_GCVT)
    {
        /* 'g' format uses 'f' notation where it can and
         * 'e' notation where the exponent is more extreme.
         * Some references indicate that it uses the more
         * compact form but the ANSI standard give an explict
         * definition: Use 'e' when the exponent is < -4
         * or where the exponent is >= ndigits.
         * The exponent is equal to decpt - 1 so this translates
         * to decpt <= -4 || decpt > ndigits
         * http://www.acm.uiuc.edu/webmonkeys/book/c_guide/2.12.html#printf
         * http://www.mkssoftware.com/docs/man3/printf.3.asp
         */
        if (decpt > -4 && decpt <= ndigits)
            fflags |= FF_FCVT;
    }
    
    // Sanitise ndigits making sure it fits buffer space.
    if (fflags & FF_FCVT)
    {
        if (!(fflags & FF_GCVT))
        {
            // For fcvt operation the number of digits is used to
            // refer to decimal places rather than significant digits.
            ndigits += decpt;
            // When there are no significant digits,
            // avoid printing too many 0's.
            if (ndigits < 0)
            {
                decpt -= ndigits;
                ndigits = 0;
            }
        }
        /* For 'f' conversions with positive DP value that would overflow
         * the buffer space, there is no way to display this so fall back
         * to 'e' format. 'f' conversion needs space for sign, point and
         * rounding digit. The point may be forced using the special flag
         * and the rounding digit may be included in the case of maximum
         * overflow.
         */
        if (decpt > BUFMAX-3)
        {
            fflags &= ~FF_FCVT;
        }
    }

    if (fflags & FF_FCVT)
    {
        // Allow space for sign, point and rounding digit.
        if (ndigits > BUFMAX-3)
            ndigits = BUFMAX-3;
        // Start placing digits after leading 0's
        if (decpt < 1)
        {
            // Number of leading zeros
            int nzero = 1 - decpt;
            // Ensure pointer is not past end of buffer
            if (nzero > BUFMAX-3)
                nzero = BUFMAX-3;
            p += nzero;
        }
    }
    else
    {
        // Allow space for sign, point and up to 3 digit exponent (E+123).
        // Rounding happens in the place where the exponent will go.
        if (ndigits > BUFMAX-7)
            ndigits = BUFMAX-7;
    }
    
    // Format digits one-by-one into the output string.
    // One extra digit is required for rounding.
    for (i = 0; i <= ndigits; i++)
    {
        // Ignore digits beyond the supported precision.
        if (i >= FLOAT_DIGITS)
        {
            *p++ = '0';
        }
        else
        {
            int n = number;
            *p++ = n + '0';
            number = (number - n) * 10;   
        }
    }
    
    // Store a pointer to the last (rounding) digit.
    pend = --p;
    // Round the result directly in the string buffer.
    // Only use the calculated digits, not trailing 0's.
    if (i > FLOAT_DIGITS)
    {
        p -= (i - FLOAT_DIGITS);
    }
    if (*p >= '5')
    {
        for (;;)
        {
            if (i == 0)
            {
                // The rounding has rippled all the way through to
                // the first digit. i.e. 9.999..9 -> 10.0
                // Just replace the first 0 with a 1 and shift the DP.
                *p = '1';
                ++decpt;
                // This increases the displayed digits for 'f' only.
                if ((fflags & (FF_FCVT|FF_GCVT)) == FF_FCVT)
                {
                    ++ndigits;
                    ++pend;
                }
                break;
            }
            // Previous digit was a rollover
            *p-- = '0';
            // Increment next digit and break out unless there is a rollover.
            if (*p != '9')
            {
                (*p)++;
                break;
            }
        }
    }

    // Insert the decimal point
    if (fflags & FF_FCVT)
    {
        int num;
        num = (decpt > 1) ? decpt : 1;
        p = buf + 1;
        for (i = 0; i < num; i++)
        {
            *p = *(p+1);
            ++p;
        }
        if (p + 1 < pend || (flags & FL_SPECIAL))
        {
            // There are digits after the DP or DP is forced.
            *p = '.';
            // Trim trailing 0's in 'g' mode.
            if ((fflags & FF_GCVT) && !(flags & FL_SPECIAL))
            {
                pend = trim_zeros(pend - 1);
            }
        }
        else
        {
            // DP at end is not required.
            --pend;
        }
    }
    else
    {
        // Decimal point is always after first digit.
        buf[1] = buf[2];
        buf[2] = '.';
        // Trim trailing 0's in 'g' mode.
        if ((fflags & FF_GCVT) && !(flags & FL_SPECIAL))
        {
            pend = trim_zeros(pend - 1);
        }
        // Add exponent
        *pend++ = (fflags & FF_UCASE) ? 'E' : 'e';
        if (--decpt < 0)
        {
            *pend++ = '-';
            decpt = -decpt;
        }
        else
        {
            *pend++ = '+';
        }
#ifndef EXP_3_DIGIT
        // Optional 3rd digit of exponent
        if (decpt > 99)
#endif
        {
            *pend++ = decpt / 100 + '0';
            decpt %= 100;
        }
        // Always print at least 2 digits of exponent.
        *pend++ = decpt / 10 + '0';
        *pend++ = decpt % 10 + '0';
    }
    // Add the sign prefix.
    p = buf + 1;
    if      (flags & FL_NEG)    *--p = '-';
#if FEATURE(USE_PLUS_SIGN)
    else if (flags & FL_PLUS)   *--p = '+';
#endif
#if FEATURE(USE_SPACE_SIGN)
    else if (flags & FL_SPACE)  *--p = ' ';
#endif
    
    *pend = '\0';   // Add null terminator
    return p;       // Start of string
}
#endif

#ifdef BASIC_PRINTF_ONLY
static printf_t doprnt(void (*func)(char c), const char *fmt, va_list ap)
#else
static printf_t doprnt(void *context, void (*func)(char c, void *context), const char *fmt, va_list ap)
#endif
{
#if FEATURE(USE_LONG)
    unsigned long uvalue;
#else
    unsigned uvalue;
#endif
    unsigned base;
#if FEATURE(USE_SPACE_PAD) || FEATURE(USE_ZERO_PAD)
    width_t width;
    width_t fwidth;
#endif
#if FEATURE(USE_PRECISION)
    width_t precision;
#else
    #define precision -1
#endif
    char convert, c;
    char *p;
    char buffer[BUFMAX+1];
#ifdef PRINTF_T
    printf_t count = 0;
#endif
    unsigned char flags;
#if FEATURE(USE_FLOAT)
    unsigned char fflags;
    double fvalue;
#endif

    buffer[BUFMAX] = '\0';

    while ((convert = GET_FORMAT(fmt)) != 0)
    {
        if (convert == '%')
        {
            p = buffer + BUFMAX;
#if FEATURE(USE_PRECISION)
            precision = -1;
#endif
#if FEATURE(USE_SPACE_PAD) || FEATURE(USE_ZERO_PAD)
            width = 0;
#endif
#if FEATURE(USE_FLOAT)
            fflags = 0;
#endif
            flags = 0;

            // Extract flag chars
            for (;;)
            {
                convert = GET_FORMAT(++fmt);
#if FEATURE(USE_ZERO_PAD)
                if (convert == '0')
                {
                    flags |= FL_ZERO_PAD;
                }
                else
#endif
#if FEATURE(USE_PLUS_SIGN)
                if (convert == '+')
                {
                    flags |= FL_PLUS;
                }
                else
#endif
#if FEATURE(USE_LEFT_JUST)
                if (convert == '-')
                {
                    flags |= FL_LEFT_JUST;
                }
                else
#endif
#if FEATURE(USE_SPACE_SIGN)
                if (convert == ' ')
                {
                    flags |= FL_SPACE;
                }
                else
#endif
#if FEATURE(USE_SPECIAL)
                if (convert == '#')
                {
                    flags |= FL_SPECIAL;
                }
                else
#endif
                    break;
            }
#if FEATURE(USE_SPACE_PAD) || FEATURE(USE_ZERO_PAD)
            // Extract width
#if FEATURE(USE_INDIRECT)
            if (convert == '*')
            {
                width = va_arg(ap, int);
                convert = GET_FORMAT(++fmt);
            }
            else
#endif
            while (convert >= '0' && convert <= '9')
            {
                width = width * 10 + convert - '0';
                convert = GET_FORMAT(++fmt);
            }
#endif
#if FEATURE(USE_PRECISION)
            // Extract precision
            if (convert == '.')
            {
                precision = 0;
                convert = GET_FORMAT(++fmt);
#if FEATURE(USE_INDIRECT)
                if (convert == '*')
                {
                    precision = va_arg(ap, int);
                    convert = GET_FORMAT(++fmt);
                }
                else
#endif
                while (convert >= '0' && convert <= '9')
                {
                    precision = precision * 10 + convert - '0';
                    convert = GET_FORMAT(++fmt);
                }
            }
#endif
#if FEATURE(USE_LONG)
            // Extract length modifier
            if (convert == 'l')
            {
                flags |= FL_LONG;
                convert = GET_FORMAT(++fmt);
            }
#endif
            switch (convert)
            {
            case 'c':
#if FEATURE(USE_SPACE_PAD)
                width = 0;
#endif
                *--p = (char) va_arg(ap, int);
                break;
            case 'd':
#if FEATURE(USE_SIGNED_I)
            case 'i':
#endif
#if FEATURE(USE_LONG)
                if (flags & FL_LONG)
                    uvalue = va_arg(ap, long);
                else
#endif
                    uvalue = va_arg(ap, int);
                base = 10;
#if FEATURE(USE_LONG)
                if ((long) uvalue < 0)
#else
                if ((int) uvalue < 0)
#endif
                {
                    flags |= FL_NEG;
                    uvalue = -uvalue;
                }
                goto number;
#if FEATURE(USE_UNSIGNED)
            case 'u':
#if FEATURE(USE_LONG)
                if (flags & FL_LONG)
                    uvalue = va_arg(ap, unsigned long);
                else
#endif
                    uvalue = va_arg(ap, unsigned);
                base = 10;
                goto number;
#endif
#if FEATURE(USE_OCTAL)
            case 'o':
#if FEATURE(USE_LONG)
                if (flags & FL_LONG)
                    uvalue = va_arg(ap, unsigned long);
                else
#endif
                    uvalue = va_arg(ap, unsigned);
                base = 8;
                goto number;
#endif
#if FEATURE(USE_HEX_LOWER)
            case 'x':
#endif
#if FEATURE(USE_HEX_UPPER)
            case 'X':
#endif
#if FEATURE(USE_HEX_LOWER) || FEATURE(USE_HEX_UPPER)
#if FEATURE(USE_LONG)
                if (flags & FL_LONG)
                    uvalue = va_arg(ap, unsigned long);
                else
#endif
                    uvalue = va_arg(ap, unsigned);
                base = 16;
#endif
            number:
#if FEATURE(USE_PRECISION)
                // Set default precision
                if (precision == -1) precision = 1;
#endif
                // Make sure options are valid.
                if (base != 10) flags &= ~(FL_PLUS|FL_NEG|FL_SPACE);
#if FEATURE(USE_SPECIAL)
                else            flags &= ~FL_SPECIAL;
#endif
                // Generate the number without any prefix yet.
#if FEATURE(USE_ZERO_PAD)
                fwidth = width;
                // Avoid formatting buffer overflow.
                if (fwidth > BUFMAX) fwidth = BUFMAX;
#endif
#if FEATURE(USE_PRECISION)
                while (uvalue || precision > 0)
#else
                if (uvalue == 0)
                {
                    // Avoid printing 0 as ' '
                    *--p = '0';
#if FEATURE(USE_ZERO_PAD)
                    --fwidth;
#endif
                }
                while (uvalue)
#endif
                {
                    c = (char) ((uvalue % base) + '0');
#if FEATURE(USE_HEX_LOWER) || FEATURE(USE_HEX_UPPER)
                    if (c > '9')
                    {
                        // Hex digits
#if FEATURE(USE_HEX_LOWER) && FEATURE(USE_HEX_UPPER)
                        if (convert == 'X') c += 'A' - '0' - 10;
                        else                c += 'a' - '0' - 10;
#elif FEATURE(USE_HEX_UPPER) || FEATURE(USE_HEX_UPPER_L)
                        c += 'A' - '0' - 10;
#else
                        c += 'a' - '0' - 10;
#endif
                    }
#endif
                    *--p = c;
                    uvalue /= base;
#if FEATURE(USE_ZERO_PAD)
                    --fwidth;
#endif
#if FEATURE(USE_PRECISION)
                    --precision;
#endif
                }
#if FEATURE(USE_ZERO_PAD)
                // Allocate space for the sign bit.
                if (flags & (FL_PLUS|FL_NEG|FL_SPACE)) --fwidth;
#if FEATURE(USE_SPECIAL)
                // Allocate space for special chars if required.
                if (flags & FL_SPECIAL)
                {
                    if (convert == 'o') fwidth -= 1;
                    else fwidth -= 2;
                }
#endif
                // Add leading zero padding if required.
                if ((flags & FL_ZERO_PAD) && !(flags & FL_LEFT_JUST))
                {
                    while (fwidth > 0)
                    {
                        *--p = '0';
                        --fwidth;
                    }
                }
#endif
#if FEATURE(USE_SPECIAL)
                // Add special prefix if required.
                if (flags & FL_SPECIAL)
                {
                    if (convert != 'o') *--p = convert;
                    *--p = '0';
                }
#endif
                // Add the sign prefix
                if      (flags & FL_NEG)    *--p = '-';
#if FEATURE(USE_PLUS_SIGN)
                else if (flags & FL_PLUS)   *--p = '+';
#endif
#if FEATURE(USE_SPACE_SIGN)
                else if (flags & FL_SPACE)  *--p = ' ';
#endif
#if FEATURE(USE_PRECISION)
                // Precision is not used to limit number output.
                precision = -1;
#endif
                break;
#if FEATURE(USE_FLOAT)
            case 'f':
                // Set default precision
                if (precision == -1) precision = 6;
                fvalue = va_arg(ap, double);
                fflags = FF_FCVT;
                p = format_float(fvalue, precision, flags, fflags, buffer);
                // Precision is not used to limit number output.
                precision = -1;
                break;
            case 'E':
                fflags = FF_UCASE;
            case 'e':
                // Set default precision
                if (precision == -1) precision = 6;
                fvalue = va_arg(ap, double);
                p = format_float(fvalue, precision + 1, flags, fflags, buffer);
                // Precision is not used to limit number output.
                precision = -1;
                break;
            case 'G':
                fflags = FF_UCASE;
            case 'g':
                fflags |= FF_GCVT;
                // Set default precision
                if (precision == -1) precision = 6;
                fvalue = va_arg(ap, double);
                p = format_float(fvalue, precision, flags, fflags, buffer);
                // Precision is not used to limit number output.
                precision = -1;
                break;
#endif
            case 's':
                p = va_arg(ap, char *);
                break;
            default:
                *--p = convert;
                break;
            }

#if FEATURE(USE_SPACE_PAD)
            // Check width of formatted text.
            fwidth = strlen(p);
            // Copy formatted text with leading or trailing space.
            // A positive value for precision will limit the length of p used.
            while ((*p && precision != 0) || width > 0)
            {
                if (((flags & FL_LEFT_JUST) || width <= fwidth) && *p && precision != 0) c = *p++;
                else c = ' ';
#else
  #if FEATURE(USE_PRECISION)
            // A positive value for precision will limit the length of p used.
            while (*p && precision != 0)
  #else
            while (*p)
  #endif
            {
                c = *p++;
#endif
#ifdef BASIC_PRINTF_ONLY
                func(c);            // Basic output function.
#else
                func(c, context);   // Output function.
#endif
#ifdef PRINTF_T
                ++count;
#endif
#if FEATURE(USE_SPACE_PAD)
                --width;
#endif
#if FEATURE(USE_PRECISION)
                if (precision > 0) --precision;
#endif
            }
        }
        else
        {
#ifdef BASIC_PRINTF_ONLY
            func(convert);              // Basic output function.
#else
            func(convert, context);     // Output function.
#endif
#ifdef PRINTF_T
            ++count;
#endif
        }
        ++fmt;
    }

#ifdef PRINTF_T
    return count;
#endif
}

// Output function for printf.
// The context is not used at present, but could be extended to include
// streams or to avoid output mixing in multi-threaded use.
#ifdef BASIC_PRINTF_ONLY
static void putout(char c)
#else
static void putout(char c, void *context)
#endif
{
    PUTCHAR_FUNC(c);
}

// printf replacement - writes to serial output using putchar.
printf_t printf(const char *fmt, ...)
{
    va_list ap;
#ifdef PRINTF_T
    int Count;
#endif

    va_start(ap, fmt);
#ifdef PRINTF_T
  #ifdef BASIC_PRINTF_ONLY
    Count = doprnt(putout, fmt, ap);
  #else
    Count = doprnt((void *)0, putout, fmt, ap);
  #endif
#else
  #ifdef BASIC_PRINTF_ONLY
    doprnt(putout, fmt, ap);
  #else
    doprnt((void *)0, putout, fmt, ap);
  #endif
#endif
    va_end(ap);
    
#ifdef PRINTF_T
    return Count;
#endif
}

#ifndef BASIC_PRINTF_ONLY
// Output function for sprintf.
// Here the context is a pointer to a pointer to the buffer.
// Double indirection allows the function to increment the buffer pointer.
static void putbuf(char c, void *context)
{
    char *buf = *((char **) context);
    *buf++ = c;
    *((char **) context) = buf;
}

//  sprintf replacement - writes into buffer supplied.
printf_t sprintf(char *buf, const char *fmt, ... )
{
    va_list ap;
#ifdef PRINTF_T
    int Count;
#endif

    va_start(ap, fmt);
#ifdef PRINTF_T
    Count = doprnt(&buf, putbuf, fmt, ap);
#else
    doprnt(&buf, putbuf, fmt, ap);
#endif
    va_end(ap);
    // Append null terminator.
    *buf = '\0';
    
#ifdef PRINTF_T
    return Count;
#endif
}
#endif

