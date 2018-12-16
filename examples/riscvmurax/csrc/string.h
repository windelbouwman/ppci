/*
 * string.h
 * String handling.
 * ANSI/ISO 9899-1990, Section 7.11.
 */

#ifndef __STRING_H__
#define	__STRING_H__

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

/* Type. */
#include <common/_size_t.h>

/* Macro. */
#include <common/_null.h>

/* Standard functions. */
void	*memcpy(void *__s1, const void *__s2, size_t __n);
void	*memmove(void *__s1, const void *__s2, size_t __n);
char	*strcpy(char *__s1, const char *__s2);
char	*strncpy(char *__s1, const char *__s2, size_t __n);
char	*strcat(char *__s1, const char *__s2);
char	*strncat(char *__s1, const char *__s2, size_t __n);
int	memcmp(const void *__s1, const void *__s2, size_t __n);
int	strcmp(const char *__s1, const char *__s2);
int	strcoll(const char *__s1, const char *__s2);
int	strncmp(const char *__s1, const char *__s2, size_t __n);
size_t	strxfrm(char *__s1, const char *__s2, size_t __n);
void	*memchr(const void *__s, int __c, size_t __n);
char	*strchr(const char *__s, int __c);
size_t	strcspn(const char *__s1, const char *__s2);
char	*strpbrk(const char *__s1, const char *__s2);
char	*strrchr(const char *__s, int __c);
size_t	strspn(const char *__s1, const char *__s2);
char	*strstr(const char *__s1, const char *__s2);
char	*strtok(char *__s1, const char *__s2);
void	*memset(void *__s, int __c, size_t __n);
char	*strerror(int __errnum);
size_t	strlen(const char *__s);

/*
 * Nonstandard functions.
 * Compile with -D__STRICT_ANSI__ or -D_POSIX_SOURCE to make these disappear.
 */
#if	!defined(__STRICT_ANSI__) && !defined(_POSIX_SOURCE)

/* BSD-isms. */
#define	bcmp(s1, s2, n)		memcmp((s2), (s1), (n))
#define	bcopy(s1, s2, n)	((char *)memmove((s2), (s1), (n)))
#define	bzero(s, n)		((void)memset((s), 0, (n)))

#if	0

/* Archaic. */
#define	index(s, c)		strchr((s), (c))
#define	rindex(s, c)		strrchr((s), (c))

#endif	/* 0 */

#endif	/* !defined(__STRICT_ANSI__) && !defined(_POSIX_SOURCE) */

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif	/* __STRING_H__ */
