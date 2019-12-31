/*
 * lib-src/ansi/math/acos.c
 * ANSI/ISO 9899-1990, Section 7.5.2.1
 *
 * double acos(double x)
 * Return the arccosine of x.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	EDOM	NaN/0.0		x < 1.0 or x > 1.0 (including [+-]Infinity)
 */

#include "mathlib.h"

#if	defined(__TCS__)
#include <ops/custom_ops.h>
#define	sqrt(x)	((double)fsqrt((float)(x)))
#endif	/* defined(__TCS__) */

double
acos(double x)
{
	double y;
	
#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	}
	/* [+-]Infinity: domain error, return NaN, from test below. */
#endif	/* defined(__IEEE_FP__) */

	if (x < -1.0 || x > 1.0) {
		errno = EDOM;
#if	defined(__IEEE_FP__)
		return _qNaN;
#else	/* defined(__IEEE_FP__) */
		return 0.0;
#endif	/* defined(__IEEE_FP__) */
	} else if (x == 0.0)
		return HALFPI;
	else if (x == 1.0)
		return 0.0;
	else if (x == -1.0)
		return PI;
	y = atan(sqrt(1.0 - (x * x)) / x );
	return (x > 0.0) ? y : y + PI;
}
