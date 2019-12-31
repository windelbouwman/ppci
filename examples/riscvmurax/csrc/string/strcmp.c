#include <string.h>

/*
 * strcmp - compare string s1 to s2
 */

int				/* <0 for <, 0 for ==, >0 for > */
strcmp(const register char *s1, const register char *s2)
{
  while (*s1 != '\0' && *s1 == *s2) {
    s1++;
    s2++;
  }

  /*
   * The following case analysis is necessary so that characters
   * which look negative collate low against normal characters but
   * high against the end-of-string NUL.
   */
  if (*s1 == '\0' && *s2 == '\0')
    return(0);
  else if (*s1 == '\0')
    return(-1);
  else if (*s2 == '\0')
    return(1);
  else
    return(*s1 - *s2);
}
