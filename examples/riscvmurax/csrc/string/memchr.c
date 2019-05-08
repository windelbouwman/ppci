/*
 * memchr - search for a byte
 *
 */

#include <string.h>

void *
memchr(const void *s, int c, size_t n)
{
	register const unsigned char *scan;
	register unsigned char uc;

	scan = s;
	uc = (unsigned char)c;
	while (n-- > 0)
		if (*scan == uc)
			return (void *)scan;
		else
			scan++;

	return NULL;
}
