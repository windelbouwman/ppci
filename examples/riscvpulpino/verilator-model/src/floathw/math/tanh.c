/*
 * lib-src/ansi/math/tanh.c
 * ANSI/ISO 9899-1990, Section 7.5.3.3.
 *
 * double tanh(double x)
 * Return the hyperbolic tangent of x.
 * Uses: tanh(x) = sinh(x) / cosh(x).
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	none	[+-]1.0		x is [+-]Infinity
 *
 * The hyperbolic tangent is approximately [+-]1.0 when abs(x) > TANH_MAXARG.
 * TANH_MAXARG should be defined appropriately for the underlying
 * double representation.  By definition,
 *	tanh(x) = (exp(x) - exp(-x)) / (exp(x) + exp(-x))
 * so tanh(x) will be 1.0 in machine arithmetic
 * when exp(x) + exp(-x) == exp(x) in machine arithmetic,
 * i.e. when exp(x) > FLT_RADIX^(DBL_MANT_DIG+1)*exp(-x).
 * By taking the log of both sides, we get
 *	x > log(FLT_RADIX^(DBL_MANT_DIG+1)) / 2
 * which defines the desired TANH_MAXARG.
 */

#include "mathlib.h"

double
tanh(double x)
{
#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	}
	/* [+-]Infinity: no error, return [+-]1.0, from test below. */
#endif	/* defined(__IEEE_FP__) */

    if (x > TANH_MAXARG || x < -TANH_MAXARG)
	    return (x > 0.0) ? 1.0 : -1.0;
    return sinh(x) / cosh(x);
}
