#include <string.h>

/*
 * strcat - append string s2 to s1
 */
char *
strcat(char *s1, const register char *s2)
{
	register char *dscan;

	for (dscan = s1; *dscan != '\0'; dscan++)
		continue;
	while ((*dscan++ = *s2++) != '\0')
		continue;
	return s1;
}
