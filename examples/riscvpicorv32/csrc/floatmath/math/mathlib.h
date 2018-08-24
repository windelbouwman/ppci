/*
 * mathlib.h
 * This header gets #included by the floating point math library routines.
 * This is the proper place to put machine dependencies.
 */

#include <errno.h>
#include <float.h>
#include <math.h>

#if	defined(__IEEE_FP__)
#include <ieee.h>
#endif	/* defined(__IEEE_FP__) */

/* Expand polynomials of orders 1, 2 or 3 directly, otherwise call _xpoly(). */
#define	_poly(order, a, x)						\
	 ((order == 1) ? (a[0] + x * a[1])				\
	: (order == 2) ? (a[0] + x * (a[1] + x * a[2]))			\
	: (order == 3) ? (a[0] + x * (a[1] + x * (a[2] + x * a[3])))	\
	: _xpoly(order, a, x))

/* Mathematical constants (representation-independent). */
#define PI		3.1415926535897932
#define TWOPI 		6.2831853071795865
#define HALFPI		1.5707963267948966
#define FOURTHPI	7.8539816339744831e-1
#define SIXTHPI		5.2359877559829887e-1

#define LOG2E		1.4426950408889634	/* log to base 2 of e */
#define LOG10E		4.3429448190325183e-1
#define SQRT2		1.4142135623730950
#define SQRT3		1.7320508075688773
#define LN2		6.9314718055994531e-1
#define LNSQRT2		3.4657359027997265e-1


/*
 * The constants below depend on the floating point representation
 * and in some cases also depend on the order of the approximating polynomial.
 */

#if	defined(__IEEE_SP_FP__)

#define	ATAN_MIN	 4.768371581e-7		/* 6th root of DBL_MIN, cf. atan.c */
#define	COS_MIN		 3.292722539e-10	/* 4th root of DBL_MIN, cf. cos.c/sin.c */
#define LN_DBL_MAX	 8.872283905e+1		/* ln(DBL_MAX) */
#define LN_DBL_MIN	-8.733654475e+1		/* ln(DBL_MIN) */
#define TANH_MAXARG	 8.664339757		/* ln(2^25)/2, cf. tanh.c */

#elif	defined(__IEEE_DP_FP__)

#define	ATAN_MIN	 5.91165426434e-20	/* 16th root of DBL_MIN, cf. atan.c */
#define	COS_MIN		 5.30343689058e-52	/* 6th root of DBL_MIN, cf. cos.c/sin.c */
#define LN_DBL_MAX	 7.09782712893e+2	/* ln(DBL_MAX) */
#define LN_DBL_MIN	-7.08039641853e+2	/* ln(DBL_MIN) */
#define TANH_MAXARG	 1.87149738751e+1	/* ln(2^54)/2, cf. tanh.c */

#else
#error	!defined(__IEEE_SP_FP__) && !defined(__IEEE_DP_FP__)
#endif	/* defined(__IEEE_SP_FP__) */

/*
 * ANSI 6.5.2.1: "The order of allocation of bitfields within a unit
 * (high-order to low-order or low-order to high-order) is
 * implementation-defined."  Bitfield allocation is high-to-low
 * on bigendian machines and low-to-high on littleendian machines in practice,
 * though there is no requirement that this be the case.
 * The definition below works on the following platforms:
 * 	Sparc and HP	acc, gcc	bigendian	high-to-low
 *	i386		gcc, msc	littleendian	low-to-high
 * There is no guarantee that it works for other C implementations,
 * since the implementation-defined bitfield allocation order may vary.
 */

#define	BF_LOW_TO_HIGH	1


/*
 * The DOUBLE union below defines the representation of an IEEE-format
 * double, either single or double precision.
 * frexp.c, ldexp.c and modf.c use this union to manipulate doubles.
 * This had better agree with what the compiler thinks a double looks like!
 * In particular, BF_LOW_TO_HIGH must be appropriately defined or undefined,
 * so that the bitfield allocation order corresponds to the double layout;
 * see the comment above.
 */

#ifdef	__IEEE_SP_FP__		/* IEEE single precision 32-bit format */

#define	EXP_BIAS	127
typedef	union	{
	double	d;
	struct	{
#if	defined(BF_LOW_TO_HIGH)
		unsigned frac_hi  : 23;
		unsigned exponent : 8;
		unsigned sign     : 1;
#else	/* defined(BF_LOW_TO_HIGH) */
		unsigned sign     : 1;
		unsigned exponent : 8;
		unsigned frac_hi  : 23;
#endif	/* defined(BF_LOW_TO_HIGH) */
	}	D;
} DOUBLE;

#endif	/* __IEEE_SP_FP__ */

#ifdef	__IEEE_DP_FP__		/* IEEE double precision 64-bit format */

#define	EXP_BIAS	1023
typedef	union	{
	double	d;
	struct	{
#if	defined(BF_LOW_TO_HIGH)
		unsigned frac_low : 32;
		unsigned frac_hi  : 20;
		unsigned exponent : 11;
		unsigned sign     : 1;
#else	/* defined(BF_LOW_TO_HIGH) */
		unsigned sign     : 1;
		unsigned exponent : 11;
		unsigned frac_hi  : 20;
		unsigned frac_low : 32;
#endif	/* defined(BF_LOW_TO_HIGH) */
	}	D;
} DOUBLE;

#endif	/* __IEEE_DP_FP__ */

