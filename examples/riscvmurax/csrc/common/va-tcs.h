/*
 * common/va-tcs.h
 * Common header for TCS <stdarg.h> and <varargs.h>.
 * The type used in va_arg must match the actual type after
 * default promotions, so e.g. va_arg(..., short) is not valid.
 */

#ifndef	__VA_TCS_H__
#define	__VA_TCS_H__

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

/* Type. */
#include <common/_va_list.h>
typedef	_LIBC_VA_LIST_	va_list;


/* Rounding macros. */
#define _va_round_var(var)	((sizeof(var)  < 4) ? 4 - sizeof(var)  : 0)
#define _va_roundup_var(var)	((sizeof(var)  < 4) ? 4		       : sizeof(var))
#define _va_round(type)		((sizeof(type) < 4) ? 4 - sizeof(type) : 0)
#define _va_roundup(type)	((sizeof(type) < 4) ? 4		       : sizeof(type))
#define _va_align(type)		((sizeof(type) + 3) & 0xFFFFFFFC)

#if	defined(__VARARGS_H__)	/* <varargs.h> */

#define va_alist    _va_alist
#define va_dcl int  _va_alist;
#define va_start(ap) ap = ((va_list) (void *) &_va_alist)

#elif	defined(__STDARG_H__)	/* <stdarg.h> */

#define va_start(ap,lastarg) (ap = (va_list) (((char *) &lastarg) + _va_roundup_var(lastarg)))

#else
#error	Do not include <common/va-tcs.h> directly; include <stdarg.h> or <varargs.h> instead.

#endif	/* defined(__VARARGS_H__) */

#define va_arg(ap,type) ((ap = ((char *) ap) + _va_align(type)), *(type *) ((char *)ap - _va_align(type)))
#define va_end(ap)	((void)0)

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif	/* __VA_TCS_H__ */

/* end of common/va-tcs.h */
