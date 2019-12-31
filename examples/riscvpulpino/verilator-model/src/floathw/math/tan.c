/*
 * lib-src/ansi/math/tan.c
 * ANSI/ISO 9899-1990, Section 7.5.2.7.
 *
 * double tan(double x)
 * Return the tangent of x.
 *
 * Reference: John F. Hart et al., "Computer Approximations,"
 * Krieger, Huntington, New York, 1968, corrected edition 1978.
 * Cf. pp. 120, 216.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	EDOM	0.0		x is [+-]Infinity
 *	ERANGE	[+-]HUGE_VAL	overflow
 */

#include "mathlib.h"

#if	defined(__IEEE_SP_FP__)

/* Hart table TAN 4242, p. 218; precision 8.20, order 1 2. */
static double P6[] = {
	 0.211849369664121e+3,
	-0.125288887278448e+2
};
static double Q6[] = {
	 0.2697350131214121e+3,
	-0.714145309347748e+2, 
	 1.0
};

#else	/* defined(__IEEE_SP_FP__) */

/* Hart table TAN 4245, p. 216; precision 17.08, order 3 3. */
static double P6[] = {
	-0.16045331195592187943926861e+5, 
	 0.1269754837658082883786072e+4,
	-0.17135185514886110932101e+2,
	 0.282087729716551031514e-1
};
static double Q6[] = {
	-0.20429550186600697853114142e+5,
	 0.5817359955465568673903419e+4,
	-0.181493103540890459934575e+3,
	 1.0
};

#endif	/* defined(__IEEE_SP_FP__) */

#define	ORDERP	((int)(sizeof(P6) / sizeof(P6[0])) - 1)
#define	ORDERQ	((int)(sizeof(Q6) / sizeof(Q6[0])) - 1)

double
tan(double x)
{
	register int invert, sign;
	double r, xsq;

#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_isInfinity(x)) {
		errno = EDOM;
		return 0.0;		/* [+-]Infinity: domain error, return 0.0 */
	}
#endif	/* defined(__IEEE_FP__) */

	/* Perform range reduction to allow polynomial approximation. */
	invert = sign = 0;
	x = modf(x / PI, &r);		/* scale x to (-1., 1.) for (-PI, PI) */
	if (x < 0.0)
		x += 1.0;		/* to [0., 1.) for [0., PI) */
	if (x > .5) {
		++sign;
		x = 1.0 - x;		/* to [0., .5] for [0., PI/2] */
	}
	if (x > .25) {
		++invert;
		x = .5 - x;		/* to [0., .25] for [0., PI/4] */
	}
	x *= 4.0;			/* to [0., 1,] */

	/* Approximate result using polynomials from Hart. */
	xsq = x * x;
	r = x * _poly(ORDERP, P6, xsq) / _poly(ORDERQ, Q6, xsq);

	/* Adjust result and return. */
	if (invert) {
		/*
		 * Watch out for overflow.
		 * 1.0 / r may not be representable even for nonzero r,
		 * but I don't see how to check for it, since e.g.
		 *	if (r < 1.0 / DBL_MAX) ...
		 * may itself cause underflow.
		 * For now, we punt and check only for r == 0.0.
		 */
		if (r == 0.0) {
			errno = ERANGE;
			return (sign) ? -HUGE_VAL : HUGE_VAL;
		}
		r = 1.0 / r;
	}
	return (sign) ? -r : r;
}
