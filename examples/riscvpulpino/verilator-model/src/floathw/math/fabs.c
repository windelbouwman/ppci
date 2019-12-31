/*
 * lib-src/ansi/math/fabs.c
 * ANSI/ISO 9899-1990, Section 7.5.6.2.
 *
 * double fabs(double x)
 * Return the absolute value of x.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	none	+Infinity	x is [+-]Infinity
 */

#include "mathlib.h"

#if	defined(__TCS__)
#include <ops/custom_ops.h>
#endif	/* defined(__TCS__) */

double
fabs(double x)
{
#if	defined(__TCS__)
	return fabsval((float)x);
#else	/* defined(__TCS__) */

#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_isInfinity(x))
		return _pInfinity;	/* [+-]Infinity: no error, return +Infinity */
#endif	/* defined(__IEEE_FP__) */

	return (x < 0.0) ? -x : x;

#endif	/* defined(__TCS__) */
}
