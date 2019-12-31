/*
 * common/_va_list.h
 * Common definition of _VA_LIST_.
 * This cannot define va_list directly because of <stdio.h>,
 * which references but does not define type va_list.
 */


#ifndef	__COMMON__VA_LIST_H__
#define	__COMMON__VA_LIST_H__

typedef	void *	_LIBC_VA_LIST_;

#endif	/* __COMMON__VA_LIST_H__ */

/* end of common/_va_list.h */
