/*
 * stdlib.h
 * General utilities.
 * ANSI/ISO 9899-1990, Section 7.10.
 */

#ifndef __STDLIB_H__
#define __STDLIB_H__

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

/* Types. */
#include <common/_size_t.h>
#include <common/_wchar_t.h>
typedef struct	{
	int	quot;		/* quotient */
	int	rem;		/* remainder */
} div_t;
typedef struct	{
	long	quot;		/* quotient */
	long	rem;		/* remainder */
} ldiv_t;

/* Macros. */
#include <common/_null.h>
#define	EXIT_FAILURE	1
#define	EXIT_SUCCESS	0
#define	RAND_MAX	32767
#define	MB_CUR_MAX	3

/* Standard functions. */
void		abort(void);
int		abs(int __j);
int		atexit(void (*__func)(void));
double		atof(const char *__nptr);
int		atoi(const char *__nptr);
long		atol(const char *__nptr);
void		*bsearch(const void *__key, const void *__base, size_t __nmemb,
			size_t __size, int (*__compar)(const void *, const void *));
void		*calloc(size_t __nmemb, size_t __size);
div_t		div(int __numer, int __denom);
void		exit(int __status);
void		free(void *__ptr);
char		*getenv(const char *__name);
long		labs(long int __j);
ldiv_t		ldiv(long int __numer, long int __denom);
void		*malloc(size_t __size);
int		mblen(const char *__s, size_t __n);
size_t		mbstowcs(wchar_t *__pwcs, const char *__s, size_t __n);
int		mbtowc(wchar_t *__pwc, const char *__s, size_t __n);
void		qsort(void *__base, size_t __nmemb, size_t __size,
			int (*__compar)(const void *, const void *));
int		rand(void);
void		*realloc(void *__ptr, size_t __size);
void		srand(unsigned int __seed);
double  	strtod(const char *__nptr, char **__endptr);
long		strtol(const char *__nptr, char **__endptr, int __base);
unsigned long	strtoul(const char *__nptr, char **__endptr, int __base);
int		system(const char *__string);
int		wctomb(char *__s, wchar_t __wchar);
size_t		wcstombs(char *__s, const wchar_t *__pwcs, size_t __n);

/* Nonstandard internal functions. */
double		_pow10(int __n);

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif	/* __STDLIB_H__ */
