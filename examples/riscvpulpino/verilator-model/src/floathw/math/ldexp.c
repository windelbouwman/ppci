/*
 * lib-src/ansi/math/ldexp.c
 * ANSI/ISO 9899-1990, Section 7.5.4.3.
 *
 * double ldexp (float x, int exp)
 * Return (x * 2 ^ exp).
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	ERANGE	[+-]Infinity	overflow
 *	ERANGE	0.0		underflow
 *	none	[+-]Infinity	x is [+-]Infinity
 *
 * This source assumes IEEE-format doubles but does not deal with denormals.
 */

#include "mathlib.h"

#if	defined(__IEEE_FP__)

double
ldexp(double x, int exp)
{
	DOUBLE u;
	int olde;	
	
	/* NaN, [+-]Infinity: domain error, return x. */
	if (_isNaN(x)) {
		errno = EDOM;		
		return x;		/* NaN: domain error, return NaN */
	} else if (_isInfinity(x))
		return x;		/* [+-]Infinity: no error, return [+-]Infinity */

	/* Nothing to do if exp is zero or if x is zero. */
	if (exp == 0 || x == 0.0)
		return x;

	/* Extract the current unbiased exponent. */
	u.d = x;
	olde = u.D.exponent - EXP_BIAS;

	/* Watch out for exponent overflow or underflow. */
	if (exp + olde > DBL_MAX_EXP - 1) {		/* overflow */
		errno = ERANGE;
		return (x < 0) ? _mInfinity : _pInfinity;
	} else if (exp + olde < DBL_MIN_EXP - 1) {	/* underflow */
		errno = ERANGE;
		return 0.0;
	}
	u.D.exponent = olde + exp + EXP_BIAS;
	return u.d;
}

#else
#error	!defined(__IEEE_FP__)

#endif	/* defined(__IEEE_FP__) */
