/*
 * lib-src/ansi/math/sqrt.c
 * ANSI/ISO 9899-1990, Section 7.5.5.2.
 *
 * double sqrt(double x)
 * Return the square root of x.
 *
 * Reference: John F. Hart et al., "Computer Approximations,"
 * Krieger, Huntington, New York, 1968, corrected edition 1978.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	EDOM	NaN/0.0		x < 0, including -Infinity
 *	none	+Infinity	x is +Infinity
 *
 * There are a lot of options available for computing sqrt(x).
 * The code below uses range reduction to [0.5, 1.0],
 * approximation by polynomial, rescaling of approximate result,
 * and then iteration using Heron's iteration (Hart formula 6.1.7).
 * Heron's iteration must be performed after rescaling,
 * otherwise rescaling may introduce low-order inaccuracy due to
 * multiplication or division by SQRT2.
 * For single precision, the approximating polynomial is
 * sufficiently accurate, but we perform an iteration
 * anyway because of possible inaccuracy introduced by scaling.
 * For double precision, one iterations is required; cf. Hart Table 6.2, p. 93.
 */
 
#include "mathlib.h"

#if	defined(__TCS__)
#include <ops/custom_ops.h>
#endif	/* defined(__TCS__) */

#if	!defined(__TCS__)
/* Hart table SQRT 0352, p. 160; precision 8.95, order 3 3. */
static	double	P5[] = {
	0.29730278874025,
	0.89403076206457e+1,
	0.211252240569754e+2,
	0.59304944591466e+1
};
static	double	Q5[] = {
	0.24934718253158e+1,
	0.177641338280541e+2,
	0.150357233129921e+2,
	1.0
};

#define	ORDERP	((int)(sizeof(P5) / sizeof(P5[0])) - 1)
#define	ORDERQ	((int)(sizeof(Q5) / sizeof(Q5[0])) - 1)
 
#define ITERATIONS	1		/* Heron's iterations required */

#endif	/* !defined(__TCS__) */

double
sqrt(double x)
{
#if	!defined(__TCS__)
	int k;
	register int kmod2, count;
	double m, y;
#endif	/* !defined(__TCS__) */

#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_ispInfinity(x))
		return x;		/* +Infinity: no error, return x */
	/* -Infinity: domain error, return NaN, from test below. */
#endif	/* defined(__IEEE_FP__) */

	/* Dispatch cases x <= 0.0. */
	if (x == 0.0)
		return 0.0;
	else if (x < 0.0) {
		errno = EDOM;		/* domain error, return NaN (or 0.0) */
#if	defined(__IEEE_FP__)
		return _qNaN;
#else	/* defined(__IEEE_FP__) */
		return 0.0;
#endif	/* defined(__IEEE_FP__) */
	}

#if	defined(__TCS__)

	/* Use the hardware floating point instruction if available. */
	return fsqrt((float)x);

#else	/* defined(__TCS__) */

	/* Extract the binary significand and approximate sqrt with polynomial. */
	m = frexp (x, &k);
	y = _poly(ORDERP, P5, m) / _poly(ORDERQ, Q5, m);

	/* Adjust approximate result according to sqrt of binary exponent. */
	if ((kmod2 = (k % 2)) < 0)
		y /= SQRT2;
	else if (kmod2 > 0)
		y *= SQRT2;
	y = ldexp(y, k / 2);

	/* Perform Heron's iteration, ITERATIONS times. */
	for (count = 0; count < ITERATIONS; count++)
		y = 0.5 * (y + (x / y));

	return y;
#endif	/* defined(__TCS__) */
}


