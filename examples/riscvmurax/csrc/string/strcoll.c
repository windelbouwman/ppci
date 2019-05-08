#include <string.h>

/*
 * strcoll(char, char) : compare two characters in the
 *                       local collating sequence.
 * Currently returns straight ASCII comparison.
 */
int
strcoll(const char *s1, const char *s2)
{
	return strcmp(s1, s2);
}
