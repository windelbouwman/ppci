/*
 * strlen - length of string (not including NUL)
 */

#include <string.h>
size_t
strlen(const char *s)
{
	register size_t count;

	count = 0;
	while (*s++ != '\0')
		count++;
	return(count);
}
