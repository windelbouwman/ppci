/*
 * float.h
 * Characteristics of floating types.
 * ANSI/ISO 9899-1990, Section 5.2.4.2.2.
*/

#ifndef	__FLOAT_H__
#define	__FLOAT_H__

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

/*
 * This header describes floating point characteristics of either
 * 32-bit or 64-bit normalized floating point values, represented
 * in the single or double precision format specified in ANSI/IEEE 754-1985.
 * _IEEE_SP_FP__ should be defined for 32-bit doubles,
 * _IEEE_DP_FP__ should be defined for 64-bit doubles.
 * _IEEE_FP__ gets defined here in either case;
 * it indicates that the floating point representation is IEEE.
 */

#if	!defined(__IEEE_SP_FP__) && !defined(__IEEE_DP_FP__)

/* Floating point for MINIMIPS is 32-bit double. */
#define	__IEEE_SP_FP__
#include <softfloat.h>

#endif	/* !defined(__IEEE_SP_FP__) && !defined(__IEEE_DP_FP__) */

/* At this point either __IEEE_SP_FP__ or __IEEE_DP_FP__ must be defined. */

#if	!defined(__IEEE_FP__)
#define	__IEEE_FP__
#endif	/* !defined(__IEEE_FP__) */

/*
 * Floating point rounding:
 *	-1	indeterminate
 *	0	towards 0
 *	1	to nearest
 *	2	towards +Infinity
 *	3	towards -Infinity
 * Any other value is implementation defined.
 */
#define FLT_ROUNDS	1			/* round to nearest	*/

#define FLT_RADIX	2			/* must be >= 2 per ISO 9899 */

/* float: 32-bit single precision IEEE representation. */
#define FLT_MANT_DIG	24			/* can be anything	*/
#define FLT_EPSILON	1.19209290E-07		/* must be <= 1E-5	*/
#define FLT_DIG		6			/* must be >= 6		*/
#define FLT_MIN_EXP	(-125)			/* can be anything	*/
#define FLT_MIN		1.17549435E-38	 	/* must be <= 1E-37	*/
#define FLT_MIN_10_EXP	(-37)			/* must be >= -37	*/
#define FLT_MAX_EXP	+128			/* can be anything	*/
#define FLT_MAX		3.40282347E+38		/* must be >= 1E+37	*/
#define FLT_MAX_10_EXP	+38			/* must be >= +37	*/

#if	defined(__IEEE_SP_FP__)

/* double: same as float, i.e. 32-bit single precision. */
#define	DBL_MANT_DIG	FLT_MANT_DIG
#define	DBL_EPSILON	FLT_EPSILON
#define	DBL_DIG		FLT_DIG
#define	DBL_MIN_EXP	FLT_MIN_EXP
#define	DBL_MIN		FLT_MIN
#define	DBL_MIN_10_EXP	FLT_MIN_10_EXP
#define	DBL_MAX_EXP	FLT_MAX_EXP
#define	DBL_MAX		FLT_MAX
#define	DBL_MAX_10_EXP	FLT_MAX_10_EXP

/* long double: same as float, i.e. 32-bit single precision. */
#define	LDBL_MANT_DIG	FLT_MANT_DIG
#define	LDBL_EPSILON	FLT_EPSILON
#define	LDBL_DIG	FLT_DIG
#define	LDBL_MIN_EXP	FLT_MIN_EXP
#define	LDBL_MIN	FLT_MIN
#define	LDBL_MIN_10_EXP	FLT_MIN_10_EXP
#define	LDBL_MAX_EXP	FLT_MAX_EXP
#define	LDBL_MAX	FLT_MAX
#define	LDBL_MAX_10_EXP	FLT_MAX_10_EXP

#else	/* defined(__IEEE_SP_FP__) */

/* double: 64-bit double precision IEEE representation. */
#define DBL_MANT_DIG	53			/* can be anything	*/
#define DBL_EPSILON	2.2204460492503131E-16	/* must be <= 1E-9	*/
#define DBL_DIG		15			/* must be >=10		*/
#define DBL_MIN_EXP	(-1021)			/* can be anything	*/
#define DBL_MIN		2.2250738585072014E-308 /* must be <= 1E-37	*/
#define DBL_MIN_10_EXP	(-307)			/* must be <= -37	*/
#define DBL_MAX_EXP	+1024			/* can be anything	*/
#define DBL_MAX		1.7976931348623157E+308	/* must be >= 1E+37	*/
#define DBL_MAX_10_EXP	+308			/* must be >= +37	*/

/* long double: same as double, i.e. 64-bit double precision. */
#define LDBL_MANT_DIG	DBL_MANT_DIG
#define LDBL_EPSILON	DBL_EPSILON
#define LDBL_DIG	DBL_DIG
#define LDBL_MIN_EXP	DBL_MIN_EXP
#define LDBL_MIN	DBL_MIN
#define LDBL_MIN_10_EXP	DBL_MIN_10_EXP
#define LDBL_MAX_EXP	DBL_MAX_EXP
#define LDBL_MAX	DBL_MAX
#define LDBL_MAX_10_EXP	DBL_MAX_10_EXP

#endif	/* defined(__IEEE_SP_FP__) */

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif /* __FLOAT_H__ */
