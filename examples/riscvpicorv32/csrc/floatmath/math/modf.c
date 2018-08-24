/*
 * lib-src/ansi/math/modf.c
 * ANSI/ISO 9899-1990, Section 7.5.4.6.
 *
 * double modf(double value, double *iptr)
 * Set *iptr to the integer part of value and return the fractional part.
 *
 * Exceptions:
 *	Error	Return		Store	Condition
 *	EDOM	NaN		NaN	value is NaN
 *	none	[+-]Infinity	0.0	value is [+-]Infinity
 *
 * This source assumes IEEE-format doubles but does not deal with denormals.
 */

#include "mathlib.h"
#include <limits.h>

#if	defined(__IEEE_FP__)

double
modf(double value, double *iptr)
{
	DOUBLE u;
	register int exp;
#if	defined(__IEEE_DP_FP__)
	register int n;
#endif	/* defined(__IEEE_DP_FP__) */

	/* Special cases: NaN and infinities. */
	if (_isNaN(value)) {
		errno = EDOM;		/* NaN: domain error */
		*iptr = value;		/* integer part is NaN */
		return value;		/* fractional part NaN */
	} else if (_isInfinity(value)) {
		*iptr = value;
		return 0.0;		/* [+-]Infinity: no error, fraction is 0 */
	}

	/* Truncation is easy if value fits in a long. */
	if (value >= (double)LONG_MIN && value <= (double)LONG_MAX) {
		*iptr = (double)(long)value;	/* truncate to integer part */
		return value - *iptr;		/* return fractional part */
	}

	/* If the unbiased exponent is large, there are no fraction bits. */
	u.d = value;
	exp = u.D.exponent - EXP_BIAS;
	if (exp >= DBL_MANT_DIG) {
		*iptr = value;
		return 0.;
	}

#if	defined(__IEEE_DP_FP__)
	/*
	 * Last resort: brute force.
	 * This code is required only for double precision representation;
	 * for single precision, value < LONG_MIN || value > LONG_MAX
	 * guarantees that exp >= DBL_MANT_DIG (i.e., there are
	 * more bits in a long than in the significand).
	 * Shift the significand right by n = DBL_MANT_DIG - 1 - exp bits,
	 * then shift it left by n bits, to clobber the fraction bits,
	 * leaving only the integer bits.
	 * Finally, subtract from the original value to get the fraction.
	 */
	n = DBL_MANT_DIG - 1 - exp;		/* shift count */
	if (n < CHAR_BIT * sizeof(unsigned long)) {
		/* Shift by fewer bits than a long; high unchanged. */
		u.D.frac_low = (u.D.frac_low >> n) << n;
	} else {
		/* Shift by more bits than a long; low gets zeroed. */
		n -= CHAR_BIT * sizeof(unsigned long);
		u.D.frac_hi = (u.D.frac_hi >> n) << n;
		u.D.frac_low = 0;
	}
	*iptr = u.d;				/* store integer part */
	return value - *iptr;			/* return fractional part */
#endif	/* defined(__IEEE_DP_FP__) */

}

#else
#error	!defined(__IEEE_FP__)

#endif	/* defined(__IEEE_FP__) */
