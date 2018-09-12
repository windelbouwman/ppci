/*
 * lib-src/ansi/math/fmod.c
 * ANSI/ISO 9899-1990, Section 7.5.6.4.
 *
 * double fmod(double x, double y)
 * Return the floating-point remainder (modulus) of x / y.
 *
 * Implementation-defined behavior for y == 0:
 * fmod() issues a domain error and returns NaN.
 *
 * Exceptions:
 *	EDOM	NaN		x or y is NaN
 *	EDOM	NaN/0.0		y is 0
 *	EDOM	NaN		x and y are [+-]Infinity
 *	EDOM	0.0		x is [+-]Infinity
 *	EDOM	x		y is [+-]Infinity
 */


#include "mathlib.h"

double
fmod(double x, double y)
{
	double intpart;

#if	defined(__IEEE_FP__)
	if (_isNaN(x) || _isNaN(y) || (_isInfinity(x) && _isInfinity(y))) {
		errno = EDOM;
		return _qNaN;		/* domain error, return NaN */
	} else if (_isInfinity(x) || _isInfinity(y)) {
		errno = EDOM;
		return (_isInfinity(x)) ? 0.0 : x;
	}
#endif	/* defined(__IEEE_FP__) */

	/* The following is implementation-defined behavior. */
	if (y == 0.0) {			/* y==0: domain error, return NaN or 0.0 */
		errno = EDOM;
#if	defined(__IEEE_FP__)
		return _qNaN;
#else	/* defined(__IEEE_FP__) */
		return 0.0;
#endif	/* defined(__IEEE_FP__) */
	}

	(void) modf(x / y, &intpart);
	return x - y * intpart;
}
