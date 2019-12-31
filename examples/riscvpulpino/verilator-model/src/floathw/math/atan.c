/*
 * lib-src/ansi/math/atan.c
 * ANSI/ISO 9899-1990, Section 7.5.2.3.
 *
 * double atan(double x)
 * Return the arctangent of x.
 *
 * Reference: John F. Hart et al., "Computer Approximations,"
 * Krieger, Huntington, New York, 1968, corrected edition 1978.
 * Cf. pp. 129, 233.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	ERANGE	0.0		x is very large (1.0 / x underflows)
 *	none	pi/2		x is +Infinity
 *	none	-pi/2		x is -Infinity
 */

#include "mathlib.h"

#if	defined(__IEEE_SP_FP__)

/* Hart table ARCTN 4940, p. 233; precision 7.69, order 3. */
static	double	C[] = {
	 .999999979773,
	-.33332423445,
	 .1993572694,
	-.128133334
};

#else	/* defined(__IEEE_SP_FP__) */

/* Hart table ARCTN 4945, p. 233; precision 16.82, order 8. */
static	double	C[] = {
	 .9999999999999999849899,		/* P0 must be first	*/
	-.333333333333299308717,
	 .1999999999872944792,
	-.142857141028255452,
	 .11111097898051048,
	-.0909037114191074,
	 .0767936869066,
	-.06483193510303,
	 .0443895157187				/* Pn must be last	*/
};

#endif	/* defined(__IEEE_SP_FP__) */

#define	ORDERC	((int)(sizeof(C) / sizeof(C[0])) - 1)

#define TAN_PI_12 0.2679491924311227074725	/*  tan (PI/12)	*/

double
atan(double x)
{

#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	}
	else if (_ispInfinity(x))
		return HALFPI;		/* +Infinity, no error, return pi/2 */
	else if (_ismInfinity(x))
		return -HALFPI;		/* -Infinity, no error, return -pi/2 */
#endif	/* defined(__IEEE_FP__) */

	if (x < 0.0)
		return -atan(-x);
	else if (x > 1.0) {
		if (x <= 1.0 / DBL_MIN)
			return HALFPI - atan (1.0 / x);
		else {			/* 1.0 / x underflows */
			errno = ERANGE;
			return 0.0;
		}
	} else if (x > TAN_PI_12)
		return SIXTHPI + atan ((x * SQRT3 - 1.0) / (SQRT3 + x));
	else if (x < ATAN_MIN)		/* x ^ (ORDERC * 2) underflows */
		return x;
	return x * _poly(ORDERC, C, x * x);
}
