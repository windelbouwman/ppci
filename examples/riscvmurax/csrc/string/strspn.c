/*
 * strspn - find length of initial segment of s consisting entirely
 * of characters from accept
 */

#include <string.h>

size_t
strspn(const char *s1, const char *s2)
{
	register const char *sscan;
	register const char *ascan;
	register size_t count;

	count = 0;
	for (sscan = s1; *sscan != '\0'; sscan++) {
		for (ascan = s2; *ascan != '\0'; ascan++)
			if (*sscan == *ascan)
				break;
		if (*ascan == '\0')
			return count;
		count++;
	}
	return count;
}
