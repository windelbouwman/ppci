/*
 * lib-src/ansi/math/frexp.c
 * ANSI/ISO 9899-1990, Section 7.5.4.2.
 *
 * frexp(double value, int *exp)
 * Return the significand of value scaled to the range [+-][.5, 1.)
 * and store the appropriate binary exponent into *exp.
 *
 * Exceptions:
 *	Error	Return	Store		Condition
 *	EDOM	NaN	0		value is NaN
 *	ERANGE	[+-]0.5	[+-]INT_MAX	value is +Infinity
 *
 * This source assumes IEEE-format doubles but does not deal with denormals.
 */

#include "mathlib.h"
#include <limits.h>

#if	defined(__IEEE_FP__)

double
frexp(double value, int *exp)
{
	DOUBLE u;

	if (_isNaN(value)) {
		errno = EDOM;
		*exp = 0;
		return value;		/* NaN: domain error, store 0, return NaN */
	} else if (_isInfinity(value)) {
		errno = ERANGE;
		*exp = INT_MAX;		/* [+-]Infinity: range error, store INT_MAX, return [+-]0.5*/
		return (value < 0.0) ? -0.5 : 0.5;
	}

	/* Zero. */
	if (value == 0.0) {
		*exp = 0;
		return value;
	}

	/*
	 * Normalized value.
	 * Extract and set exponent using union DOUBLE, cf. "mathlib.h".
	 * A double with an exponent of EXP_BIAS - 1 is in the range [.5, 1.).
	 */
	u.d = value;
	*exp = (int)u.D.exponent - (EXP_BIAS - 1);	/* extract and unbias */
	u.D.exponent = EXP_BIAS - 1;			/* adjust */
	return u.d;
}

#else
#error	!defined(__IEEE_FP__)

#endif	/* defined(__IEEE_FP__) */
