/*
 * strcspn - find length of initial segment of s consisting entirely
 * of characters not from s2
 */

#include <string.h>

size_t
strcspn(const char *s1,  const char *s2)
{
	register const char *scan;
	register const char *rscan;
	register size_t count;

	count = 0;
	for (scan = s1; *scan != '\0'; scan++) {
		for (rscan = s2; *rscan != '\0';)	/* ++ moved down. */
			if (*scan == *rscan++)
				return(count);
		count++;
	}
	return count;
}
