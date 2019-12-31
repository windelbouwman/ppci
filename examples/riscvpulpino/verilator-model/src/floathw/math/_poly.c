/*
 * libc/math/_poly.c
 * Internal math library function.
 *
 * double _xpoly(int order, double *coeffs, double x)
 * Return coeff[0] + x * coeff[1] + ... + x ^ order * coeff[order].
 *
 * This computes _xpoly in the more efficient form:
 *	 _xpoly(x) = coeff[0] + x * (coeff[1] + x * (coeff[2] + ...+ x * coeff[n])).
 */

#include "mathlib.h"

double
_xpoly(register int order, register double *coefp, double x)
{
	register double d;

	coefp += order;
	d = *coefp--;
	while (order-- > 0)
		d = *coefp-- + (x * d);
	return d;
}
