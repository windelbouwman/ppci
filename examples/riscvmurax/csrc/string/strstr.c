/*
 * strstr - find first occurrence of s2 in s
 */
#include <string.h>

char *				/* found string, or NULL if none */
strstr(const char *s1, const char *s2)
{
	register const char *scan;
	register size_t len;
	register char firstc;

	/*
	 * The odd placement of the two tests is so "" is findable.
	 * Also, we inline the first char for speed.
	 * The ++ on scan has been moved down for optimization.
	 */
	firstc = *s2;
	if (firstc == 0)
	  return (char *)s1;	/* as per ANSI */
	len = strlen(s2);
	for (scan = s1; *scan != firstc || strncmp(scan, s2, len) != 0; )
		if (*scan++ == '\0')
			return NULL;
	return (char *)scan;
}
