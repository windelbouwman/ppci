#include <string.h>

/*
 * memcmp - compare bytes
 */
int				/* <0, == 0, >0 */
memcmp(const void *s1, const void *s2, size_t n)
{
	register const char *scan1;
	register const char *scan2;

	scan1 = s1;
	scan2 = s2;
	while (n-- > 0)
		if (*scan1 == *scan2) {
			scan1++;
			scan2++;
		} else
			return *scan1 - *scan2;

	return 0;
}
