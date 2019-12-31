/*
 * lib-src/ansi/math/cosh.c
 * ANSI/ISO 9899-1990, Section 7.5.3.1.
 *
 * double cosh(double x)
 * Return the hyperbolic cosine of x.
 * Uses: cosh(x) = 0.5 * (exp(x) + exp(-x)).
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	ERANGE	HUGE_VAL	exp(x) or exp(-x) overflows
 *	none	+Infinity	x is [+-]Infinity
 */

#include "mathlib.h"

double
cosh(double x)
{
#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_isInfinity(x))
		return _pInfinity;	/* [+-]Infinity: no error, return +Infinity */
#endif

	if (x > LN_DBL_MAX || x < LN_DBL_MIN) {
		errno = ERANGE;
		return HUGE_VAL;
	}
	x = exp(x);
	return 0.5 * (x + 1.0 / x);
}
