/*
 * stddef.h
 * Common definitions.
 * ANSI/ISO 9899-1990, Section 7.1.6.
 */

#ifndef	__STDDEF_H__
#define	__STDDEF_H__

/* Types. */
typedef	int	ptrdiff_t;
#include <common/_size_t.h>
#include <common/_wchar_t.h>

/* Macros. */
#include <common/_null.h>
#define	offsetof(type, member)	((size_t)(&((type *)0)->member))

#if	defined(__cplusplus)
extern	"C"	{
}
#endif	/* defined(__cplusplus) */

#endif	/* __STDDEF_H__ */
