
#include <string.h>

/*
 * strxfrm(s1, s2, size) : transform a string from "local" form.
 *
 * This currently only works for ANSI locale
 *
 * The return value 'r' is the size of the transformed
 * string (w/o the null byte), if r >= n, the contents of s1 are indeterminate.
 *
 * (Since the transform is a no-op, r is always strlen(s2))
 */


size_t
strxfrm(char *s1, const char *s2, size_t n)
{
	int r;

	if ( n )
		strncpy(s1, s2, n);

	r = strlen(s2);

	return r;
}

  
