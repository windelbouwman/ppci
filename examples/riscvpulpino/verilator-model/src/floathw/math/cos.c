/*
 * libc/math/cos.c
 * ANSI/ISO 9899-1990, Section 7.5.2.5.
 *
 * double cos(double x)
 * Return the cosine of x.
 *
 * Reference: John F. Hart et al., "Computer Approximations,"
 * Krieger, Huntington, New York, 1968, corrected edition 1978.
 * Cf. pp. 119, 210.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	EDOM	1.0		x is [+-]Infinity
 */

#include "mathlib.h"

#if	defined(__TCS__)
#include <ops/custom_ops.h>
#define	sqrt(x)	((double)fsqrt((float)(x)))
#endif	/* defined(__TCS__) */

#if	defined(__IEEE_SP_FP__)

/* Hart table COS 3841, p. 210; precision 10.10, order 2 2. */
static double P2[] = {
	 0.29711957557904981e+4,
	-0.8358601134548263e+3,
	 0.232683849892453e+2
};
static double Q2[] = {
	 0.29711957560278108e+4,
	 0.805313349644432e+2,
	 1.0
};

#else	/* !defined(__IEEE_SP_FP__) */

/* Hart table COS 3843, p. 210; precision 16.18, order 3 3. */
static double P2[] = {
	 0.12905394659037374438e+7,
	-0.37456703915723204710e+6,
	 0.13432300986539084285e+5,
	-0.11231450823340933092e+3
};
static double Q2[] = {
	 0.12905394659037373590e+7,
	 0.23467773107245835052e+5,
	 0.20969518196726306286e+3,
	 1.0
};

#endif	/* !defined(__IEEE_SP_FP__) */

#define	ORDERP	((int)(sizeof(P2) / sizeof(P2[0])) - 1)
#define	ORDERQ	((int)(sizeof(Q2) / sizeof(Q2[0])) - 1)

double
cos(double x)
{
	double y;

#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_isInfinity(x)) {
		errno = EDOM;
		return 1.0;		/* [+-]Infinity: domain error, return 1.0 */
	}
#endif	/* defined(__IEEE_FP__) */

	if (x < -PI || x > PI) {
		x = fmod(x, TWOPI);
		if (x > PI)
			x = x - TWOPI;
		 else if (x < -PI)
			x = x + TWOPI;
	}
	if (x > HALFPI)
		return -(cos(x - PI));
	else if (x < -HALFPI)
		return -(cos(x + PI));
	else if (x > FOURTHPI)
		return sin(HALFPI - x);
	else if (x < -FOURTHPI)
		return sin(HALFPI + x);
	else if (x < COS_MIN && x > -COS_MIN)
		return sqrt(1.0 - (x * x));
	y = x / FOURTHPI;
	return _poly(ORDERP, P2, y * y) / _poly(ORDERQ, Q2, y * y);
}

/* end of libc/math/cos.c */

