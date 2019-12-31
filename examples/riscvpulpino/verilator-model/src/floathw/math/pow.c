/*
 * lib-src/ansi/math/pow.c
 * ANSI/ISO 9899-1990, Section 7.5.5.1.
 *
 * double pow(double x, double y)
 * Return x raised to the y power.
 *
 * For noninteger y, compute x ^ y as exp(y * log(x)).
 * For integer y, compute x ^ y by iterated multiplication, for accuracy.
 *
 * Exceptions:
 * Too many cases, here is a summary, not including NaNs.
 *					y:
 * 		-Inf	Int<0 Nonint<0	0.0	Int>0 Nonint>0	+Inf
 *	-Inf	NaN	NaN	NaN	1	NaN	NaN	NaN
 *	 <0	NaN	ok	NaN	1	ok	NaN	NaN
 *  x:	0.0	NaN	NaN/0	NaN/0	NaN/1	0	0	0
 *	 >0	0	ok	ok	1	ok	ok	+Inf
 *	+Inf	0	0	0	1	+Inf	+Inf	+Inf
 * Additional errors may be returned by log() or exp(), q.v.
 */

#include "mathlib.h"

/* Return values, NaN if IEEE. */
#if	defined(__IEEE_FP__)
#define	NAN_OR_0	_qNaN
#define	NAN_OR_1	_qNaN
#else	/* defined(__IEEE_FP__) */
#define	NAN_OR_0	0.0
#define	NAN_OR_1	1.0
#endif	/* defined(__IEEE_FP__) */

double
pow(double x, double y )
{
	double r;
	register long i;
	register int invert;

#if	defined(__IEEE_FP__)
	/* Handle special cases where x or y is NaN or [+-]Infinity. */
	if (_isNaN(x) || _isNaN(y)) {
		errno = EDOM;
		return _qNaN;			/* NaN: domain error, return NaN */
	} else if (_ispInfinity(x))
		return (y > 0) ? x : (y == 0.0) ? 1.0 :  0.0;
	else if (_ismInfinity(x)) {
		if (y == 0)
			return 1.0;
		errno = EDOM;
		return _qNaN;
	} else if (_ispInfinity(y)) {
		if (x >= 0.0)
			return (x == 0.0) ? x : y;
		errno = EDOM;
		return _qNaN;
	} else if (_ismInfinity(y)) {
		if (x > 0.0)
			return 0.0;
		errno = EDOM;
		return _qNaN;
	}
#endif	/* defined(__IEEE_FP__) */

	/* Deal with easy cases. */
	if (x == 0.0) {
		if (y > 0.0)
			return 0.0;
		errno = EDOM;		/* x == 0 && y <= 0, domain error */
		return (y == 0.0) ? NAN_OR_1 : NAN_OR_0; /* 0^0 returns 1.0 */
	} else if (y == 0.0)
		return 1.0;

	/* If y is not integral, use exp() and log(). */
	if (modf(y, &r) != 0.0) {	/* y not integer */
		if (x > 0.0)
			return exp(y * log(x));
		errno = EDOM;
		return NAN_OR_0;	/* x < 0, y not integer, domain error */
	}

	/* y is integral, but make sure it fits in a long. */
	i = (long)y;
	if ((double)i != y)
		return exp(y * log(x));

	/*
	 * Compute result by iterated multiplication, for accuracy.
	 * This should do overflow checking.
	 */
	if (i < 0) {
		invert = 1;
		i = -i;
	} else
		invert = 0;
	for (r = 1.0; i != 0; i >>= 1) {
		if ((i & 1) != 0)
			r *= x;
		x *= x;
	}
	return (invert) ? 1.0 / r : r;
}
