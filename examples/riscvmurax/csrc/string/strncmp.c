#include <string.h>

/*
 * strncmp - compare at most n characters of string s1 to s2
 */

int				/* <0 for <, 0 for ==, >0 for > */
strncmp(const char*s1, const char *s2, size_t n)
  {
	const char *scan1;
	const char *scan2;
	int count;

	scan1 = s1;
	scan2 = s2;
	count = n;
	while (--count >= 0 && *scan1 != '\0' && *scan1 == *scan2) {
		scan1++;
		scan2++;
	}
	if (count < 0)
		return(0);

	/*
	 * The following case analysis is necessary so that characters
	 * which look negative collate low against normal characters but
	 * high against the end-of-string NUL.
	 */

	if (*scan1 == '\0' && *scan2 == '\0')
		return(0);
	else if (*scan1 == '\0')
		return(-1);
	else if (*scan2 == '\0')
		return(1);
	else
		return(*scan1 - *scan2);
  }
