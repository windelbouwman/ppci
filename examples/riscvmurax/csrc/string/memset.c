/*
 * libc/string/memset.c
 * ANSI/ISO 9899-1990, section 7.11.6.1.
 *
 * [atw] written in a (moderately) efficient fashion,
 * using word moves where possible.
 * N.B. This assumes:
 *	sizeof(unsigned long)==4 and
 *	CHAR_BIT==8 and
 *	ptr % 3 == 0 guarantees that ptr is ulong-aligned.
 */

#include <string.h>

void *
#ifdef __TCS_V2__ /* version V2.0 */
memset(void *t, int c, size_t n)
#else /* __TCS_V2__ */
memset(void *s, int c, size_t n)
#endif /* __TCS_V2__ */
{
	size_t		l, head;
	unsigned long	aword;
	void		*p;
#ifdef __TCS_V2__ /* version V2.0 */
	char		*s = t;
#endif /* __TCS_V2__ */
    
	p = s;

	if (n > 3) {
		/* Set leading bytes as necessary to force word alignment. */
		if (head = ((size_t)s) & 0x3) {
			head = 4 - head;	/* bytes to next word boundary */
			n -= head;		/* adjust count */
			while (head--)		/* set leading bytes */
				*(char *)s++ = (char)c;
		}

		l = (n >> 2);			/* # of unsigned longs */
		n &= 0x3;			/* # of residual bytes */

		/* Construct an unsigned long word of the desired value. */
		aword = (unsigned char)c;
		aword |= (aword <<  8);
		aword |= (aword << 16);

		/* Set words. */
		while (l--) {
#ifdef __TCS_V2__ /* version V2.0 */
			*(unsigned long *)s = aword;
			s += sizeof(unsigned long);
#else /* __TCS_V2__ */
			*((unsigned long *)s)++ = aword;
#endif /* __TCS_V2__ */
		}
	}

	/* Set trailing bytes if necessary. */
	while (n--)
		*(char *)s++ = (char)c;

	return p;
}

/* end of memset.c */
