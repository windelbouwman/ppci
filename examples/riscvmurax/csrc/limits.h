/*
 * limits.h
 * Sizes of integral types.
 * ANSI/ISO 9899-1990, Section 5.2.4.2.1.
 */

#ifndef __LIMITS_H__
#define __LIMITS_H__

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

#define	CHAR_BIT	8		/* bits per char */
#define	CHAR_MAX	SCHAR_MAX
#define	CHAR_MIN	SCHAR_MIN
#define	INT_MAX		0x7FFFFFFF
#define	INT_MIN		(-2147483647-1)
#define	LONG_MAX	0x7FFFFFFFL
#define	LONG_MIN	(-2147483647L-1L)
#define	MB_LEN_MAX	3		/* max length of multibyte character */
#define	SCHAR_MAX	127
#define	SCHAR_MIN	(-128)
#define	SHRT_MAX	32767
#define	SHRT_MIN	(-32768)
#define	UCHAR_MAX	255
#define	UINT_MAX	0xFFFFFFFFU
#define	USHRT_MAX	65535
#define	ULONG_MAX	0xFFFFFFFFUL

#define	_BSD_LINE_MAX		2048

#define	_POSIX_ARG_MAX		4096
#define	_POSIX_CHILD_MAX	6
#define	_POSIX_LINK_MAX		8
#define	_POSIX_MAX_CANON	255
#define	_POSIX_MAX_INPUT	255
#define	_POSIX_NAME_MAX		14
#define	_POSIX_NGROUPS_MAX	0
#define	_POSIX_OPEN_MAX		16
#define	_POSIX_PATH_MAX		255
#define	_POSIX_PIPE_BUF		512

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif	/* __LIMITS_H__ */

