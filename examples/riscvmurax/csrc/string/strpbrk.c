/*
 * strpbrk - find first occurrence of any char from breakat in s
 */

#include <string.h>

char *				/* found char, or NULL if none */
strpbrk(const char *s1, const char *s2)
{
	register const char *sscan;
	register const char *bscan;

	for (sscan = s1; *sscan != '\0'; sscan++) {
		for (bscan = s2; *bscan != '\0';)	/* ++ moved down. */
			if (*sscan == *bscan++)
				return (char *)sscan;
	}
	return NULL;
}
