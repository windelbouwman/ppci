/*
 * bcopy(): bcopy() is guaranteed to work correctly even if source 
 *	      and dest overlap.
 */

#ifdef __TCS_V2__ /* version V2.0 */
bcopy(const void *t2, void *t1, int n)
#else /* __TCS_V2__ */
bcopy(const void *s2, void *s1, int n)
#endif /* __TCS_V2__ */
{
#ifdef __TCS_V2__ /* version V2.0 */
	const char *lasts, *s2 = t2;
	char *lastd, *s1 = t1;
#else /* __TCS_V2__ */
	const void *lasts;
	void *lastd;
#endif /* __TCS_V2__ */
	
	if (n == 0) {
		return;
	} /* check for no movement. */

	/*
	 * check for overlap; if not, use the
	 * (presumably faster) memcpy routine.
	 */
	lasts = s2 + (n-1);
	lastd = s1 + (n-1);
	if (((s1 < s2) || (s1 > lasts)) &&
			((lastd < s2) || (lastd > lasts)))
		__memcpy(s1, s2, n);

	/*
	 * no joy; copy the strings byte-by-byte
	 * in the appropriate order (increasing byte
	 * addresses if s1<s2, decreasing if s1>s2).
	 */
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
}
