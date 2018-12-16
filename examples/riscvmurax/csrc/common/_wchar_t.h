/*
 * common/_wchar_t.h
 * Common definition of wchar_t.
 */

#ifndef	__COMMON__WCHAR_T_H__
#define	__COMMON__WCHAR_T_H__

#if !(defined _WCHAR_T || defined __cplusplus)
/*In C++ wchar_t is a built-in type.*/
typedef	int wchar_t;	/* was unsigned shor (Jan) */
#endif

#endif	/* __COMMON__WCHAR_T_H__ */
