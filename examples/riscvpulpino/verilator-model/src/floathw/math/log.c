/*
 * lib-src/ansi/math/log.c
 * ANSI/ISO 9899-1990, Section 7.5.4.4.
 *
 * double log(double x)
 * Return the natural log of x.
 *
 * Reference: John F. Hart et al., "Computer Approximations,"
 * Krieger, Huntington, New York, 1968, corrected edition 1978.
 * Cf. pp. 111, 195.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN
 *	EDOM	NaN/-HUGE_VAL	x < 0, including -Infinity
 *	ERANGE	-HUGE_VAL	x is 0
 *	none	+Infinity	x is +Infinity
 */

#include "mathlib.h"

#if	defined(__IEEE_SP_FP__)

/* Hart table LOGE 2701, p. 195; precision 8.48, order 1 1. */
static double P3[] = {
	-0.331355617479e+1,
	 0.89554061525
};
static double Q3[] = {
	-0.165677797691e+1,
	 1.0
};

#else	/* defined(__IEEE_SP_FP__) */

/* Hart table LOGE 2705, p. 195; precision 19.38, order 3 3. */
static double P3[] = {
	-0.24013917955921050986e+2,
	 0.30957292821537650062e+2,
	-0.96376909336868659324e+1,
	 0.4210873712179797145
};
static double Q3[] = {
	-0.12006958977960525471e+2,
	 0.19480966070088973051e+2,
	-0.89111090279378312337e+1,
	 1.0000
};

#endif	/* defined(__IEEE_SP_FP__) */

#define	ORDERP	((int)(sizeof(P3) / sizeof(P3[0])) - 1)
#define	ORDERQ	((int)(sizeof(Q3) / sizeof(Q3[0])) - 1)

double
log(double x)
{
	int k;
	double s, z, q;

#if	defined(__IEEE_FP__)
	if (_isNaN(x) || _ismInfinity(x)) {
		errno = EDOM;
		return _qNaN;		/* NaN, -Infinity: domain error, return NaN */
	} else if (_ispInfinity(x))
		return x;		/* +Infinity: no error, return +Infinity */
#endif	/* defined(__IEEE_FP__) */

	if (x < 0.0) {
		errno = EDOM;		/* EDOM error, return NaN or -HUGE_VAL */
#ifdef	__IEEE_FP__
		return _qNaN;
#else
		return -HUGE_VAL;
#endif
	} else if (x == 0.0) {
		errno = ERANGE;
		return -HUGE_VAL;
	}

	s = SQRT2 * frexp (x, &k);
	z = (s - 1.0) / (s + 1.0);
	q = z * (_poly (ORDERP, P3, z * z) / _poly (ORDERQ, Q3, z * z));
	return k * LN2 - LNSQRT2 + q;
}
