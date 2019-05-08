#include <string.h>

/*
 * strncat - append at most n characters of string s2 to s1
 */
char *
strncat(char *s1, const char *s2, size_t n)
{
	char *dscan;
	const char *sscan;
	int count;

	for (dscan = s1; *dscan != '\0'; dscan++)
		continue;
	sscan = s2;
 	count = n;
	while (*sscan != '\0' && --count >= 0)
		*dscan++ = *sscan++;
	*dscan++ = '\0';
	return s1;
}
