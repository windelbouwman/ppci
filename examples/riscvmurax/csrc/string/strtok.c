/* strok:
 * Get next token from string s (NULL on 2nd, 3rd, etc. calls),
 * where tokens are nonempty strings separated by runs of
 * chars from delim.  Writes NULs into s to end tokens.  delim need not
 * remain constant from call to call.
 */

#include <string.h>

char *				/* NULL if no token left */
strtok(char *s1, register const char *s2)
{
	register char *scan;
	char *tok;
	register const char *dscan;
	static char **scanpointp;

	if (s1 == NULL && *scanpointp == NULL)
		return(NULL);
	if (s1 != NULL)
		scan = s1;
	else
		scan = *scanpointp;

	/*
	 * Scan leading delimiters.
	 */
	for (; *scan != '\0'; scan++) {
		for (dscan = s2; *dscan != '\0'; dscan++)
			if (*scan == *dscan)
				break;
		if (*dscan == '\0')
			break;
	}
	if (*scan == '\0') {
		*scanpointp = NULL;
		return(NULL);
	}

	tok = scan;

	/*
	 * Scan token.
	 */
	for (; *scan != '\0'; scan++) {
		for (dscan = s2; *dscan != '\0';)	/* ++ moved down. */
			if (*scan == *dscan++) {
				*scanpointp = scan+1;
				*scan = '\0';
				return(tok);
			}
	}

	/*
	 * Reached end of string.
	 */
	*scanpointp = NULL;
	return(tok);
}
