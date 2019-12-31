/*
 * lib-src/ansi/math/atan2.c
 * ANSI/ISO 9899-1990, Section 7.5.2.4.
 *
 * double atan2(double y,double x)
 * Return the arctangent of y/x, in the appropriate quadrant.
 *
 * Exceptions:
 *	EDOM	NaN		x is NaN or y is NaN
 *	EDOM	NaN		x is [+-]Infinity and y is [+-]Infinity
 *	EDOM	NaN		x is 0.0 and y is [+-]Infinity
 *	EDOM	NaN		x is 0.0 and y is 0.0
 *	none	0.0		x is [+-]Infinity, y not [+-]Infinity
 *	none	[+-]pi/2	x is nonzero, y is [+-]Infinity
 */

#include "mathlib.h"

double
atan2(double y, double x)
{
#if	defined(__IEEE_FP__)
	if (_isNaN(x)
	 || _isNaN(y)
	 || (_isInfinity(x) && _isInfinity(y))
	 || (x == 0.0 && _isInfinity(y))) {
		errno = EDOM;
		return _qNaN;		/* domain error, return NaN */
	} else if (_isInfinity(x))
		return 0.0;		/* x is [+-]Infinity, no error, return 0.0 */
	else if (_isInfinity(y)) {
		if (_ispInfinity(y))
			return (x > 0.0) ? HALFPI : -HALFPI;
		else
			return (x > 0.0) ? -HALFPI : HALFPI;
	}
#endif	/* defined(__IEEE_FP__) */

	if (x == 0.0) {
		if (y == 0.0) {		/* both 0.0: domain error, return NaN or 0.0 */
			errno = EDOM;
#if	defined(__IEEE_FP__)
			return _qNaN;
#else	/* defined(__IEEE_FP__) */
			return 0.0;
#endif	/* defined(__IEEE_FP__) */
		}
		return (y > 0) ? HALFPI : -HALFPI;
	} else if (x > 0.0)
		return atan (y/x);
	else if (y > 0.0)
		return atan (y/x) + PI;
	else
		return atan (y/x) - PI;
}
