/*
 *  strrchr 
 *
 * Notes:  A naive implementation.  Should use the 960
 *         "scanbyte" instruction and be inlined for benchmarking.
 *
 * Andy Wilson, 3-Oct-89.
 */

#include <string.h>

char *
  strrchr(const char *s, int c)
{
  char *lastc=(char *)0;

  /*
   * are we searching for a null?  if so,
   * this routine is the same as strchr.
   */

  if (c=='\0')
    return strchr(s, c);

  /*
   * If not, walk the string until we find a null,
   * returning a pointer to the last char to match 'c'.
   */

  while (*s != '\0')
    {
      if (*s == c)
	lastc = (char *)s;
      s++;
    }
  return lastc;
}
