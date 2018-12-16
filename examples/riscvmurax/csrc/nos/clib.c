/*
    FreeRTOS V8.2.3 - Copyright (C) 2015 Real Time Engineers Ltd.
    All rights reserved

    VISIT http://www.FreeRTOS.org TO ENSURE YOU ARE USING THE LATEST VERSION.

    This file is part of the FreeRTOS distribution and was contributed
    to the project by Technolution B.V. (www.technolution.nl,
    freertos-riscv@technolution.eu) under the terms of the FreeRTOS
    contributors license.

    FreeRTOS is free software; you can redistribute it and/or modify it under
    the terms of the GNU General Public License (version 2) as published by the
    Free Software Foundation >>>> AND MODIFIED BY <<<< the FreeRTOS exception.

    ***************************************************************************
    >>!   NOTE: The modification to the GPL is included to allow you to     !<<
    >>!   distribute a combined work that includes FreeRTOS without being   !<<
    >>!   obliged to provide the source code for proprietary components     !<<
    >>!   outside of the FreeRTOS kernel.                                   !<<
    ***************************************************************************

    FreeRTOS is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE.  Full license text is available on the following
    link: http://www.freertos.org/a00114.html

    ***************************************************************************
     *                                                                       *
     *    FreeRTOS provides completely free yet professionally developed,    *
     *    robust, strictly quality controlled, supported, and cross          *
     *    platform software that is more than just the market leader, it     *
     *    is the industry's de facto standard.                               *
     *                                                                       *
     *    Help yourself get started quickly while simultaneously helping     *
     *    to support the FreeRTOS project by purchasing a FreeRTOS           *
     *    tutorial book, reference manual, or both:                          *
     *    http://www.FreeRTOS.org/Documentation                              *
     *                                                                       *
    ***************************************************************************

    http://www.FreeRTOS.org/FAQHelp.html - Having a problem?  Start by reading
    the FAQ page "My application does not run, what could be wrong?".  Have you
    defined configASSERT()?

    http://www.FreeRTOS.org/support - In return for receiving this top quality
    embedded software for free we request you assist our global community by
    participating in the support forum.

    http://www.FreeRTOS.org/training - Investing in training allows your team to
    be as productive as possible as early as possible.  Now you can receive
    FreeRTOS training directly from Richard Barry, CEO of Real Time Engineers
    Ltd, and the world's leading authority on the world's leading RTOS.

    http://www.FreeRTOS.org/plus - A selection of FreeRTOS ecosystem products,
    including FreeRTOS+Trace - an indispensable productivity tool, a DOS
    compatible FAT file system, and our tiny thread aware UDP/IP stack.

    http://www.FreeRTOS.org/labs - Where new FreeRTOS products go to incubate.
    Come and try FreeRTOS+TCP, our new open source TCP/IP stack for FreeRTOS.

    http://www.OpenRTOS.com - Real Time Engineers ltd. license FreeRTOS to High
    Integrity Systems ltd. to sell under the OpenRTOS brand.  Low cost OpenRTOS
    licenses offer ticketed support, indemnification and commercial middleware.

    http://www.SafeRTOS.com - High Integrity Systems also provide a safety
    engineered and independently SIL3 certified version for use in safety and
    mission critical applications that require provable dependability.

    1 tab == 4 spaces!
*/

#include <stdarg.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>
#include "clib.h"
#include "murax.h"

//#define static_assert(cond) switch(0) { case 0: case !!(long)(cond): ; }

size_t
strnlen(const char *s, size_t maxlen)
{
 return(strlen (s) < maxlen ? strlen (s) : maxlen);
}


/* Writes char to frontend. */
#undef putchar
int putchar(int ch)
{
	static char buf[64];
	static int buflen = 0;

	buf[buflen++] = ch;

	if (ch == '\n' || buflen == sizeof(buf)) {
		char* bufPtr = buf;
		while(buflen != 0){
			//TEST_COM_BASE[0] = *(bufPtr++);  //TODO !!!!
            uart_write(UART,*(bufPtr++));
			buflen--;
		}
	}

	return 0;
}
/*-----------------------------------------------------------*/

/* Writes number to putchar. */
static void printnum(void (*putch)(int, void**), void **putdat,
		unsigned long num, unsigned base, int width, int padc)
{
	unsigned digs[sizeof(num) * CHAR_BIT];
	int pos = 0;

	for(;;) {
		digs[pos++] = num % base;
		if (num < base)
			break;
		num /= base;
	}

	while (width-- > pos){
		putch(padc, putdat);
	}

	while (pos-- > 0){
		putch(digs[pos] + (digs[pos] >= 10 ? 'a' - 10 : '0'), putdat);
	}
}
/*-----------------------------------------------------------*/

/* Returns unsigned integer from argument list. */
static unsigned long getuint(va_list *ap, int lflag)
{
	if (lflag >= 2) {
		return va_arg(*ap, unsigned long);
	} else if (lflag) {
		return va_arg(*ap, unsigned long);
	} else {
		return va_arg(*ap, unsigned int);
	}
}
/*-----------------------------------------------------------*/

/* Returns signed integer from argument list. */
static long getint(va_list *ap, int lflag)
{
	if (lflag >= 2) {
			return va_arg(*ap, long);
	} else if (lflag) {
			return va_arg(*ap, long);
	} else {
			return va_arg(*ap, int);
	}
}
/*-----------------------------------------------------------*/

/* Format and print a string. */
static void vFormatPrintString(void (*putch)(int, void**), void **putdat,
			const char *fmt, va_list ap)
{
	register const char* p;
	const char* last_fmt;
	register int ch;
	unsigned long num;
	int base, lflag, width, precision;
	char padc;

	while (1) {
		while ((ch = *(unsigned char *) fmt) != '%') {
			if (ch == '\0')
				return;
			fmt++;
			putch(ch, putdat);
		}
		fmt++;

		// Process a %-escape sequence
		last_fmt = fmt;
		padc = ' ';
		width = -1;
		precision = -1;
		lflag = 0;
		reswitch: switch (ch = *(unsigned char *) fmt++) {

			/* flag to pad on the right */
			case '-':
				padc = '-';
				goto reswitch;

				/* flag to pad with 0's instead of spaces */
			case '0':
				padc = '0';
				goto reswitch;

				/* width field */
			case '1':
			case '2':
			case '3':
			case '4':
			case '5':
			case '6':
			case '7':
			case '8':
			case '9':
				for (precision = 0;; ++fmt) {
					precision = precision * 10 + ch - '0';
					ch = *fmt;
					if (ch < '0' || ch > '9')
						break;
				}
				goto process_precision;

			case '*':
				precision = va_arg(ap, int);
				goto process_precision;

			case '.':
				if (width < 0)
					width = 0;
				goto reswitch;

			case '#':
				goto reswitch;

				process_precision: if (width < 0)
					width = precision, precision = -1;
				goto reswitch;

				/* long flag (doubled for long) */
			case 'l':
				lflag++;
				goto reswitch;

				/* character */
			case 'c':
				putch(va_arg(ap, int), putdat);
				break;

				/* string */
			case 's':
				if ((p = va_arg(ap, char *)) == NULL)
					p = "(null)";
				if (width > 0 && padc != '-')
					for (width -= strnlen(p, precision); width > 0; width--)
						putch(padc, putdat);
				for (; (ch = *p) != '\0' && (precision < 0 || --precision >= 0); width--) {
					putch(ch, putdat);
					p++;
				}
				for (; width > 0; width--)
					putch(' ', putdat);
				break;

				/* (signed) decimal */
			case 'd':
				num = getint(&ap, lflag);
				if ((long) num < 0) {
					putch('-', putdat);
					num = -(long) num;
				}
				base = 10;
				goto signed_number;

				/* unsigned decimal */
			case 'u':
				base = 10;
				goto unsigned_number;

				/* (unsigned) octal */
			case 'o':
				base = 8;
				goto unsigned_number;

				/* pointer */
			case 'p':
				//static_assert(sizeof(long) == sizeof(void*))
				;
				lflag = 1;
				putch('0', putdat);
				putch('x', putdat);
				/* no break, fall through to hexidecimal */
				/* (unsigned) hexadecimal */
			case 'x':
				base = 16;
				unsigned_number: num = getuint(&ap, lflag);
				signed_number: printnum(putch, putdat, num, base, width, padc);
				break;

				/* escaped '%' character */
			case '%':
				putch(ch, putdat);
				break;

				/* unrecognized escape sequence */
			default:
				putch('%', putdat);
				fmt = last_fmt;
				break;
		}
	}
}
/*-----------------------------------------------------------*/

/* Cause normal process termination  */
void exit(int code)
{
	//TODO syscall(SYS_exit, code, 0, 0);
	for(;;) { }
}
/*-----------------------------------------------------------*/

/* formatted output conversion to frontend */
int printf(const char* fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);

	vFormatPrintString((void*) putchar, 0, fmt, ap);

	va_end(ap);
	return 0; // incorrect return value, but who cares, anyway?
}
/*-----------------------------------------------------------*/

static void sprintf_putch(int ch, void** data) {
		char** pstr = (char**) data;
		**pstr = ch;
		(*pstr)++;
	}

/* formatted output conversion to string */
int sprintf(char* str, const char* fmt, ...)
{
	va_list ap;
	char* str0 = str;
	va_start(ap, fmt);
	

	vFormatPrintString(sprintf_putch, (void**) &str, fmt, ap);
	*str = 0;

	va_end(ap);
	return str - str0;
}
/*-----------------------------------------------------------*/
