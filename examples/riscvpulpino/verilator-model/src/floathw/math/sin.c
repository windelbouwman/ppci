/*
 * libc/math/sin.c
 * ANSI/ISO 9899-1990, Section 7.5.2.6.
 *
 * double sin(double x)
 * Return the sine of x.
 *
 * Reference: John F. Hart et al., "Computer Approximations,"
 * Krieger, Huntington, New York, 1968, corrected edition 1978.
 * Cf. pp. 118, 199-200.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	EDOM	0.0		x is [+-]Infinity
 */

#include "mathlib.h"

#if	defined(__IEEE_SP_FP__)

/* Hart table SIN 3062, p. 200; precision 14.62, order 3 2. */
static double P4[] = {
         0.12752317157040252689531e+5,
	-0.1148319659730019252866e+4,
	 0.24491788946981444987e+2,
	-0.1586433575585969204
};
static double Q4[] = {
         0.16236754491348387146302e+5,
	 0.207188411599011955321e+3,
	 1.0
};

#else	/* !defined(__IEEE_SP_FP__) */

/* Hart table SIN 3063, p. 200; precision 17.59, order 3 3. */
static double P4[] = {
	 0.20664343336995858240e+7,
	-0.18160398797407332550e+6,
	 0.35999306949636188317e+4,
	-0.20107483294588615719e+2
};
static double Q4[] = {
	0.26310659102647698963e+7,
	0.39270242774649000308e+5,
	0.27811919481083844087e+3,
	1.0
};

#endif	/* !defined(__IEEE_SP_FP__) */

#define	ORDERP	((int)(sizeof(P4) / sizeof(P4[0])) - 1)
#define	ORDERQ	((int)(sizeof(Q4) / sizeof(Q4[0])) - 1)

double
sin(double x)
{
	double y;

#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_isInfinity(x)) {
		errno = EDOM;
		return 0.0;		/* [+-]Infinity: domain error, return 0.0 */
	}

#endif	/* defined(__IEEE_FP__) */

	if (x < -PI || x > PI) {
		x = fmod (x, TWOPI);
		if (x > PI)
			x -= TWOPI;
		else if (x < -PI)
			x += TWOPI;
	}
	if (x > HALFPI)
		return -(sin (x - PI));
	else if (x < -HALFPI)
		return -(sin (x + PI));
	else if (x > FOURTHPI)
		return cos (HALFPI - x);
	else if (x < -FOURTHPI)
		return -(cos (HALFPI + x));
	else if (x < COS_MIN && x > -COS_MIN)
		return x;
	y = x / FOURTHPI;
	return y * (_poly (ORDERP, P4, y * y) / _poly(ORDERQ, Q4, y * y));
}

/* end of libc/math/sin.c */
