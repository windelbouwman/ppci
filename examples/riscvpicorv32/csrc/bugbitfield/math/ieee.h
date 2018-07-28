/*
 * ieee.h
 * ANSI/IEEE 754-1985, "IEEE Standard for Binary Floating-Point Arithmetic".
 * Defines simple tests for infinities and Nans
 * and declares external globals contining infinities, NaNs, and minus zero.
*/

#ifndef	__IEEE_H__
#define	__IEEE_H__

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

/* Nonstandard globals. */
extern	double	_mInfinity;	/* -Infinity		*/
extern	double	_pInfinity;	/* +Infinity		*/
extern	double	_qNaN;		/* quiet NaN		*/
extern	double	_sNaN;		/* a signalling NaN	*/

/* Nonstandard macros. */
#define	_isNaN(d)	(float32_is_nan(d))
#define	_ispInfinity(d)	((d) == _pInfinity)
#define	_ismInfinity(d)	((d) == _mInfinity)
#define	_isInfinity(d)	(_ispInfinity(d) || _ismInfinity(d))
#define	_ismZero(d)	(*((unsigned long *)&d) == 0x80000000UL)

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif /* __IEEE_H__ */
