/*
 * math.h
 * Mathematics.
 * ANSI/ISO 9899-1990, Section 7.5.
 */

#ifndef  __MATH_H__
#define  __MATH_H__

#include <ieee.h>			/* to define _pInfinity */
//#include <softfloat.h>

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

/* Macro. */
#define HUGE_VAL	_pInfinity 	/* positive infinity */

/* Standard functions. */
double	acos	(double __x);
double	asin	(double __x);
double	atan	(double __x);
double	atan2	(double __y, double __x);
double	ceil	(double __x);
double	cos	(double __x);
double	cosh	(double __x);
double	exp	(double __x);
double	fabs	(double __x);
double	floor	(double __x);
double	fmod	(double __x, double __y);
double	frexp	(double __value, int *__exp);
double	ldexp	(double __x, int __exp);
double	log	(double __x);
double	log10	(double __x);
double	modf	(double __value, double *__iptr);
double	pow	(double __x, double __y);
double	sin	(double __x);
double	sinh	(double __x);
double	sqrt	(double __x);
double	tan	(double __x);
double	tanh	(double __x);

/* Internal function. */
double	_xpoly	(int __order, double *__coefp, double __x);

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif	/* __MATH_H__ */
