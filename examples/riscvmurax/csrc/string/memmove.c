/*
 * memmove(): memmove() is guaranteed to work correctly even if source 
 *	      and dest overlap.
 */

#include <string.h>

void *
#ifdef __TCS_V2__ /* version V2.0 */
memmove(void *t1, const void *t2, size_t n)
#else /* __TCS_V2__ */
memmove(void *s1, const void *s2, size_t n)
#endif /* __TCS_V2__ */
{
#ifdef __TCS_V2__ /* version V2.0 */
	const char *lasts, *s2 = t2;
	char *lastd, *s1 = t1;
	char *retval;
#else /* __TCS_V2__ */
	const void *lasts;
	void *lastd;
	void *retval;
#endif /* __TCS_V2__ */
	
	if (n == 0) {
		return s1;
	} /* check for no movement. */

	/*
	 * check for overlap; if not, use the
	 * (presumably faster) memcpy routine.
	 */
	lasts = s2 + (n-1);
	lastd = s1 + (n-1);
	if (((s1 < s2) || (s1 > lasts)) &&
			((lastd < s2) || (lastd > lasts)))
		return memcpy(s1, s2, n);

	/*
	 * no joy; copy the strings byte-by-byte
	 * in the appropriate order (increasing byte
	 * addresses if s1<s2, decreasing if s1>s2).
	 */
	retval = s1;
	if (s1 < s2)
		while (n--)
#ifdef __TCS_V2__ /* version V2.0 */
			*s1++ = *s2++;
#else /* __TCS_V2__ */
			*(char *)s1++ = *(char *)s2++;
#endif /* __TCS_V2__ */
	else
		while (n--)
#ifdef __TCS_V2__ /* version V2.0 */
			*lastd-- = *lasts--;
#else /* __TCS_V2__ */
			*(char *)lastd-- = *(char *)lasts--;
#endif /* __TCS_V2__ */
	return retval;
}
