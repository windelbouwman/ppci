/*
 * lib-src/ansi/math/log10.c
 * ANSI/ISO 9899-1990, Section 7.5.4.5.
 *
 * double log10(double x)
 * Return the common logarithm of x.
 * Computes log10(x) using:
 *	log10(x) = log10(e) * log(x).
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	EDOM	NaN		x < 0.0, including -Infinity (cf. log.c)
 *	ERANGE	-HUGE_VAL	x is 0 (cf. log.c)
 *	none	+Infinity	x is +Infinity
 */

#include "mathlib.h"

double
log10(double x)
{
#if	defined(__IEEE_FP__)
	if (_isNaN(x) || _ismInfinity(x)) {
		errno = EDOM;
		return _qNaN;		/* NaN, -Infinity: domain error, return NaN */
	} else if (_ispInfinity(x))
		return x;		/* +Infinity: no error, return +Infinity */
#endif	/* defined(__IEEE_FP__) */

	return LOG10E * log(x);
}
