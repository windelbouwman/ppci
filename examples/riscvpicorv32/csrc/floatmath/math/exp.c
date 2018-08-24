/*
 * lib-src/ansi/math/exp.c
 * ANSI/ISO 9899-1990, Section 7.5.4.1.
 *
 * double exp(double x)
 * Return e to the xth power.
 *
 * Reference: John F. Hart et al., "Computer Approximations,"
 * Krieger, Huntington, New York, 1968, corrected edition 1978.
 * Cf. pp. 102, 171.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	ERANGE	HUGE_VAL	exp(x) overflows
 *	ERANGE	0.0		exp(x) underflows
 *	none	+Infinity	x is +Infinity
 *	none	0.0		x is -Infinity
 */
 
#include "mathlib.h"
#if	defined(__IEEE_SP_FP__)

/* Hart table EXPB 1063, p. 171; precision 10.03, order 1 1. */
static	double	P1[] = {
	0.72152891511493e+1,
	0.576900723731e-1
};
static	double	Q1[] = {
	0.208189237930062e+2,
	1.0
};

#else	/* defined(__IEEE_SP_FP__) */

/* Hart table EXPB 1067, p. 171; precision 18.08, order 2 2. */
static	double	P1[] = {
	0.1513906799054338915894328e+04,
	0.20202065651286927227886e+02,
	0.23093347753750233624e-01
};
static	double	Q1[] = {
	0.4368211662727558498496814e+04,
	0.233184211427481623790295e+03,
	1.0
};

#endif	/* defined(__IEEE_SP_FP__) */

#define	ORDERP	((int)(sizeof(P1) / sizeof(P1[0])) - 1)
#define	ORDERQ	((int)(sizeof(Q1) / sizeof(Q1[0])) - 1)

double
exp(double x)
{
	register int flag;
	double r, intpart, xsq, a, b;
 
#if	defined(__IEEE_FP__)
	if (_isNaN(x)) {
		errno = EDOM;
		return x;		/* NaN: domain error, return NaN */
	} else if (_ispInfinity(x))
		return x;		/* +Infinity: no error, return +Infinity */
	else if (_ismInfinity(x))
		return 0.0;		/* -Infinity: no error, return 0.0 */
#endif	/* defined(__IEEE_FP__) */

	/* Watch out for overflow or underflow. */
	if (x > LN_DBL_MAX) {		/* overflow: range error, return HUGE_VAL */
		errno = ERANGE;
		return HUGE_VAL;
	} else if (x <= LN_DBL_MIN) {	/* underflow: ERANGE error, return 0.0 */
		errno = ERANGE;
		return 0.0;
	}

	/*
	 * Compute e ^ x as 2 ^ (x * LOG2E).
	 * Reduce the exponent to the range [0, .5],
	 * then use approximating polynomial as in Hart.
	 */
#if	1
	/*
	 * The code used here may give more accurate results on some
	 * machines than the more obvious alternative below;
	 * for example, on i80x87, intermediate results are kept
	 * in 80-bit registers rather than rounded to 64-bit doubles.
	 * On most machines, though, it makes no difference.
	 */
    
	(void)modf(x * LOG2E, &intpart); /* find intpart */
	x = x * LOG2E - intpart;	/* find fraction */
#else
	x = modf(x * LOG2E, &intpart);
#endif
	if (x < 0.0) {
		x += 1.0;		/* force fraction positive */
		intpart -= 1.0;		/* and adjust exponent accordingly */
	}
	if (x > 0.5) {			/* reduce x to range [0, .5] */
		r = SQRT2;
		x -= 0.5;
	} else
		r = 1.0;
	xsq = x * x;    
	a = _poly(ORDERQ, Q1, xsq);
	b = x * _poly(ORDERP, P1, xsq);	
	return ldexp(((r * (a + b)) / (a - b)), (int)intpart);
}
