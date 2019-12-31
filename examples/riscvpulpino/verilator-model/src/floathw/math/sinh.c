/*
 * lib-src/ansi/math/sinh.c
 * ANSI/ISO 9899-1990, Section 7.5.3.2.
 *
 * double sinh(double x)
 * Return the hyperbolic sine of x.
 * Uses: sinh(x) = 0.5 * (exp(x) - 1.0 / exp(x)).
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	ERANGE	HUGE_VAL	exp(x) overflows
 *	ERANGE	-HUGE_VAL	exp(-x) overflows
 *	none	[+-]Infinity	x is [+-]Infinity
 */

#include "mathlib.h"

double
sinh(double x)
{
#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_isInfinity(x))
		return x;		/* [+-]Infinity: no error, return x */
#endif	/* defined(__IEEE_FP__) */

	if (x > LN_DBL_MAX) {
		errno = ERANGE;
		return HUGE_VAL;
	} else if (x < LN_DBL_MIN) {
		errno = ERANGE;
		return -HUGE_VAL;
	}
	x = exp(x);
	return 0.5 * (x - (1.0 / x));
}
