#include <string.h>

/*
 * strncpy - copy at most n characters of string s2 to s1
 */
char *
strncpy(char *s1, const char *s2, size_t n)
{
	char *dscan;
	const char *sscan;
	size_t count;
	
	dscan = s1;
	sscan = s2;
	count = n;
	while (count > 0) {
		--count;
		if((*dscan++ = *sscan++) == '\0')
			break;
	}
	while (count-- > 0)
		*dscan++ = '\0';
	return s1;
}
