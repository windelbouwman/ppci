/*
 * strchr : 
 *
 * Notes:  A naive implementation.  Should use the 960
 *         "scanbyte" instruction and be inlined for benchmarking.
 *
 * Andy Wilson, 3-Oct-89.
 */

#include <string.h>

char *
  strchr(const char* s, int c)
{
  do
    {
      if (*s==c)	/* note that 0 is a valid char to search for */
	return (char *)s;
    }
  while (*s++ != '\0');

  return (char *)NULL;
}
