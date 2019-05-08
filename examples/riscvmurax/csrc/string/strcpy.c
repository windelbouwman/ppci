#include <string.h>

/*
 * strcpy - copy string s2 to s1
 */
char *			
strcpy( register char *s1, const register char *s2)
{
	register char *p;
	register unsigned ch;

	p = s1;
	do {
		ch = *s2++;
		*p++ = ch;
	} while (ch);

	return s1;
}
