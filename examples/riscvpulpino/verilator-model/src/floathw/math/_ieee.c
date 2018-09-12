/*
 * _ieee.c
 * Defines four IEEE 754-1985 format double globals, accessed as:
 *	double	_mInfinity;	-Infinity
 *	double	_pInfinity;	+Infinity
 *	double	_qNaN;		quiet NaN
 *	double	_sNaN;		signalling NaN
 * But this source lies about the types below,
 * initializing each with the appropriate bit pattern
 * as an unsigned long or array of unsigned long (cough cough).
 * This won't work with link-time type checking, obviously.
 * N.B. Assumes 32-bit unsigned long!
 */

/* Do not include <ieee.h>, because this source lies about the types. */
#include <float.h>		/* to set __IEEE*__ */

#if	defined(__IEEE_SP_FP__)

unsigned long	_mInfinity	= 0xFF800000;
unsigned long	_pInfinity	= 0x7F800000;
unsigned long	_qNaN		= 0x7FC00000;
unsigned long	_sNaN		= 0x7F800001;

#elif	defined(__IEEE_DP_FP__)

#if	defined(__MIPSEL__)		/* e.g. i386 */

/*
 * The memory storage order of each unsigned long element below
 * is of course also little-endian, so the layout as bytes is actually
 *	uchar	_mInfinity[8]	= {  0, 0, 0, 0, 0, 0, 0xF0, 0xFF };
 * etc., as expected.
 */
unsigned long	_mInfinity[2]	= { 0x00000000, 0xFFF00000 };
unsigned long	_pInfinity[2]	= { 0x00000000, 0x7FF00000 };
unsigned long	_qNaN[2]	= { 0x00000000, 0x7FF80000 };
unsigned long	_sNaN[2]	= { 0x00000001, 0x7FF00000 };

#else	/* defined(__MIPSEL__) */

unsigned long	_mInfinity[2]	= { 0xFFF00000, 0x00000000 };
unsigned long	_pInfinity[2]	= { 0x7FF00000, 0x00000000 };
unsigned long	_qNaN[2]	= { 0x7FF80000, 0x00000000 };
unsigned long	_sNaN[2]	= { 0x7FF00000, 0x00000001 };

#endif	/* defined(__MIPSEL__) */

#else
#error	!defined(__IEEE_SP_FP__) && !defined(__IEEE_DP_FP__)

#endif	/* defined(__IEEE_SP_FP__) */

/* end of _ieee.c  */
