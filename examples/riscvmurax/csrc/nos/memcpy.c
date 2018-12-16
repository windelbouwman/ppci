/*
 * memcpy(): copy memory.
 */

#include <string.h>

void *
memcpy(void *t1, const void *t2, size_t n)
{
  char *s1 = t1;
  const char *s2 = t2;

  /*
   * finish up with byte moves.
   */
  while (n--)
    *s1++ = *s2++;

  return t1;
}

void *
__memcpy(void *t1, const void *t2, size_t n)
{
	return memcpy(t1, t2, n);
}
