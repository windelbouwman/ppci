/*
 * libc/stdlib/malloc.c
 *
 * Memory allocation as per ANSI/ISO 9899-1990:
 *	void	*calloc(size_t nmemb, size_t size)	7.10.3.1
 *	void	free(void *ptr)				7.10.3.2
 *	void	*malloc(size_t size)			7.10.3.3
 *	void	*realloc(void *ptr, size_t size)	7.10.3.4
 *
 * Implementation defined behavior:
 *	If the size of the space requested is zero, return NULL.
 *
 * Uses the boundary-tag allocation method (first fit) with roving pointer.
 * Calls sbrk() as necessary to grow the memory arena by grabbing from the heap,
 * but does not assume that successive sbrk() calls return contiguous memory.
 *
 * Each block (p) in the arena is marked with a size word (p->size)
 * with its low bit (MARKBIT) set if the block is in use.
 * The size|mark word is replicated in the losize word of the successor block
 * to facilitate joining adjacent freed blocks and thus avoid fragmentation.
 * The block can hold a malloc'ed block of up to p->size - OVERHEAD bytes.
 * The free list is maintained as a doubly linked list:
 * each free block contains pointers to previous free and next free block,
 * to facilitate simple addition and deletion of free blocks.
 * The bottom losize word and top size word of each allocated arena contain
 * a 0 | MARKBIT word to indicate a used block of size 0.
 *
 * Reference:
 *	Harry R. Lewis and Larry Denenberg, "Data Structures and
 *	Their Algorithms," Harper Collins, 1991, Chapter 10, pp. 361ff.
 */

#define EXCL_START()	/**/
#define EXCL_END()	/**/

#define FN_ALLOC_CHECK	alloc_check
#define FN_ALLOC_STATS	alloc_stats
#define FN_CALLOC	calloc
#define FN_FREE		free
#define FN_MALLOC	malloc
#define FN_REALLOC	realloc
#define FN_ADD_FREE	add_free

/* Compilation options. */
#define	ALLOC_CHECK	0		/* include code to check/dump free list	*/
#define	ALLOC_STATS	0		/* include code to keep statistics	*/
#define	ALLOC_ERRORS	0		/* report invalid free(), realloc()	*/

#if	ALLOC_CHECK || ALLOC_ERRORS || ALLOC_STATS
#include <stdio.h>
#endif	/* ALLOC_CHECK || ALLOC_ERRORS || ALLOC_STATS */

#include <stdlib.h>
#include <stddef.h>
#include <sys/types.h>

#ifndef offsetof
#define   offsetof(s, m)  (size_t)(&(((s *)0)->m))
#endif

/* Memory block structure. */
typedef	struct	block {
	uint		losize;			/* size | MARKBIT of predecessor */
	uint		size;			/* size | MARKBIT		*/
	struct	block	*prev;			/* previous free block (if free) */
	struct	block	*next;			/* next free block (if free)	*/
} BLOCK;

/* Manifest constants. */
#define	MARKBIT		1			/* used mark for size field	*/
#define	MINBLOCK	(sizeof(BLOCK))		/* minimum block size		*/
#define	OVERHEAD	(offsetof(BLOCK, prev))	/* block overhead (if used)	*/

/*
 * Tuneable manifest constants.
 * N.B. grow_free() forces each allocated BLOCK *p to be ALIGNMENT-aligned,
 * but then the code below currently implicitly assumes the resulting
 * malloc pointer memory(p) to be ALIGNMENT-aligned too.
 * Changing ALIGNMENT here to a larger value here will ->not<- guarantee
 * ALIGNMENT-aligned malloc values unless the code is modified.
 */
#define	ALIGNMENT	(sizeof(uint))		/* result alignment (2^n)	*/
#define	SBRK_ROUNDUP	2048			/* sbrk() arg roundup (2^n)	*/

/*
 * Macros:
 *	add(p)		add p to doubly linked freelist
 *	blockp(vp)	convert void * malloc pointer to BLOCK *
 *	bump(p, n)	bump pointer p by n bytes; result is BLOCK *
 *	clearmarks(p)	clear the used marks of p
 *	delete(p)	delete p from doubly linked list
 *	is_free(p)	iff p is free
 *	is_predfree(p)	iff predecessor of p is free
 *	memory(p)	convert BLOCK * to void * malloc pointer
 *	needed(n)	min allocation block size for n byte malloc
 *	pred(p)		predecessor of p
 *	pred_size(p)	size of predecessor of p
 *	roundup(n, m)	round n up to size m; assumes m is power of 2
 *	setmarks(p)	set used marks of p
 *	setsizes(p, n)	set size of p and losize of successor of p to n
 *	succ(p)		successor of p
 */
#define	add(p)		(p)->prev = freelist;		\
			(p)->next = freelist->next;	\
			freelist->next = freelist->next->prev = (p); \
			alloc_stat(++n_blocks_free);	\
			alloc_stat(n_bytes_free += (p)->size)
#define	blockp(vp)	bump(vp, -OVERHEAD)
#define	bump(p, n)	((BLOCK *)(((char *)(p)) + (n)))
#define	clearmarks(p)	(p)->size &= ~MARKBIT; succ(p)->losize &= ~MARKBIT
#define	delete(p)	(p)->prev->next = (p)->next;	\
			(p)->next->prev = (p)->prev;	\
			alloc_stat(--n_blocks_free);	\
			alloc_stat(n_bytes_free -= (p)->size)
#define	is_free(p)	(((p)->size & MARKBIT) == 0)
#define	is_predfree(p)	(((p)->losize & MARKBIT) == 0)
#define	memory(p)	((void *)bump(p, OVERHEAD))
#define	needed(n)	(((n) + OVERHEAD < MINBLOCK) ? MINBLOCK : (n) + OVERHEAD)
#define	pred(p)		bump((p), -pred_size(p))
#define	pred_size(p)	((p)->losize & ~MARKBIT)
#define	roundup(n, m)	(((n) + (m) - 1) & ~((m) - 1))
#define	setmarks(p)	(succ(p)->losize = (p)->size = (p)->size | MARKBIT)
#define	setsizes(p, n)	(p)->size = (n); succ(p)->losize = (p)->size
#define	succ(p)		bump((p), ((p)->size & ~MARKBIT))

#if	ALLOC_CHECK
/* Check that args are equal, print message and die if not. */
#define	check(a1, a2)	if ((a1) != (a2)) {			\
				fprintf(stderr, "_alloc_check: %s = %d but %s = %d\n", \
					#a1, a1, #a2, a2);	\
				abort();			\
			}
#endif	/* ALLOC_CHECK */

#if	ALLOC_STATS
#define	alloc_stat(arg)	(arg)
#else	/* !ALLOC_STATS */
#define	alloc_stat(arg)
#endif	/* !ALLOC_STATS */


/* Forward. */
static	BLOCK	*grow_free(size_t size);
extern	void	_add_free(void *ptr, size_t size);
#if	ALLOC_CHECK
extern	void	_alloc_check(int dflag, int fflag);
#endif	/* ALLOC_CHECK */
#if	ALLOC_STATS
extern	void	_alloc_stats(void);
#endif	/* ALLOC_STATS */
extern	void	_swap_mm(void **new_malloc, void **new_free, void **new_realloc);
static	void	_free(void *ptr);
static	void	*_malloc(size_t size);
static	void	*_realloc(void *ptr, size_t size);

/* Static locals. */
static	BLOCK	*arena_end;
static	BLOCK	*arena_start;
static	BLOCK	freelist0 = { 0, 0, &freelist0, &freelist0 };
static	BLOCK	*freelist = &freelist0;
static	BLOCK	*rover = &freelist0;
#if	ALLOC_STATS
static	uint	_add_free_called;
static	uint	n_blocks;
static	uint	n_blocks_free;
static	uint	n_blocks_unalloc;
static	uint	n_bytes;
static	uint	n_bytes_free;
static	uint	n_bytes_unalloc;
static	uint	n_calls_calloc;
static	uint	n_calls_free;
static	uint	n_calls_malloc;
static	uint	n_calls_realloc;
static	uint	n_calls_sbrk;
static	uint	n_calls_sbrk_failed;
#endif	/* ALLOC_STATS */

/* Local functions. */

#if 0
/*
 * Grab enough space for an ALIGNMENT-aligned block of at least size bytes,
 * using sbrk() to allocate space from the heap.
 * This assumes that successive successful sbrk() calls
 * return monotonically increasing pointer values.
 * It does ->not<- assume that successive sbrk() calls
 * will return adjoining memory; that is, it allows the user to use sbrk()
 * calls intermixed with malloc() calls, provided the user does not try to
 * shrink the heap with a negative sbrk() argument.
 * Return (BLOCK *)NULL on failure.
 */
static
BLOCK *
grow_free(size_t size)
{
	size_t	n, m;
	BLOCK	*p, *q;
	void	*vp;

	alloc_stat(++n_calls_sbrk);

	n = needed(size);		/* adjust for minsize and overhead */
	n += OVERHEAD;			/* for prev losize + next size if noncontiguous arena */
	n = roundup(n, SBRK_ROUNDUP);	/* round up for sbrk() request */

	/*
	 * Check the current break and force it to be ALIGNMENT-aligned.
	 * N.B. Here we do assume that the following two or three sbrk()
	 * calls return contiguous memory.
	 */
	m = (((uint)sbrk(0)) & (ALIGNMENT - 1));
	if (m != 0 && sbrk(ALIGNMENT - m) == (void *)-1) {
		alloc_stat(++n_calls_sbrk_failed);
		return (BLOCK *)NULL;	/* alignment allocation failed */
	}

	/*
	 * Make sure the request is not unreasonably large.
	 * sbrk() with a negative arg shrinks the heap, which is not good.
	 */
	if ((unsigned int)INT_MAX < (unsigned int)n)
		return (BLOCK *)NULL;	/* no way */
		
	/* Grab an ALIGNMENT-aligned space for n bytes, using sbrk(). */
	if ((vp = sbrk(n)) == (void *)-1) {
		alloc_stat(++n_calls_sbrk_failed);
		return (BLOCK *)NULL;	/* allocation failed */
	}

	/* Allocation succeeded, make the memory a block p on the freelist. */
	alloc_stat(n_bytes += n);
	p = blockp(vp);
	if (p != arena_end) {
		/*
		 * The allocated memory p is not contiguous with arena_end.
		 * Mark the unallocated area as a used block.
		 */
		alloc_stat(++n_blocks);
		alloc_stat(++n_blocks_unalloc);
		p = (BLOCK *)vp;
		if (arena_end == 0) {
			/* First time, set arena_start, predecessor size 0. */
			arena_start = p;
			m = 0;
			alloc_stat(n_bytes_unalloc += OVERHEAD);
		} else {
			/* Mark unallocated block as used block of size m. */
			m = (char *)p - (char *)arena_end;
			arena_end->size = m | MARKBIT;
			alloc_stat(n_bytes += m - OVERHEAD);	/* count the hole */
			alloc_stat(n_bytes_unalloc += m);
		}
		p->losize = m | MARKBIT;	/* predecessor size m, marked used */
		n -= OVERHEAD;		/* adjust usable size of new block */
	}

	/* Initialize the new memory block. */
	setsizes(p, n);			/* usable size of new block */
	arena_end = succ(p);		/* save new arena_end */
	arena_end->size = 0 | MARKBIT;	/* "successor" size 0, marked used */

	/* If the predecessor block is free, coalese. */
	if (is_predfree(p)) {
		/* Coalese new block q with predecessor free block p. */
		alloc_stat(n_bytes_free += n);
		p = pred(p);
		setsizes(p, p->size + n);
	} else {
		alloc_stat(++n_blocks);
		add(p);			/* add new block p to the free list */
	}
	return p;
}
#endif

/* Global functions. */

/*
 * Add a non-malloc'ed piece of memory to the free list.
 * Does not check for overlap with the existing arena, caveat utilitor!
 * If we kept a list of the blocks added by this routine,
 * we could modify _alloc_check() to check everything correctly.
 * Instead, _alloc_check() currently only checks the arena grown by
 * grow_free(), and its checks are relaxed once _add_free() is called.
 */
void
FN_ADD_FREE(void *ptr, size_t size)
{
	BLOCK	*p;

	/* Force the memory to be ALIGNMENT-aligned. */
	while (size > 0 && (((uint)ptr) & (ALIGNMENT - 1)) != 0) {
		ptr = (void *)((uint)ptr + 1);
		--size;
	}

	/* Make sure the block is large enough to matter. */
	if (size < MINBLOCK + OVERHEAD)
		return;

	/* Mark the block appropriately and add it to the free list. */
#if	ALLOC_CHECK
	_add_free_called = 1;		/* because _alloc_check() needs to know */
#endif	/* ALLOC_CHECK */
	p = (BLOCK *)ptr;
	size -= OVERHEAD;		/* for empty marker at end */
	p->losize = 0 | MARKBIT;	/* predecessor size 0 */
	setsizes(p, size);		/* size of added block */
	succ(p)->size = 0 | MARKBIT;	/* successor size 0 */
	add(p);				/* add to free list */
}

#if	ALLOC_CHECK
/*
 * Sanity check the memory arena and the free list.
 * Dump the memory arena if dflag,
 * dump the free list if fflag.
 */
void
FN_ALLOC_CHECK(int dflag, int fflag)
{
	BLOCK	*p;
	size_t	n, nbytes, nblocks, nblocksfree, nbytesfree, largest;
	char	*s;

	/* Check the memory arena. */
	if ((p = arena_start) != NULL) {
		if (dflag)
			printf("Memory arena:\n");
		nbytes = nblocks = nblocksfree = nbytesfree = 0;
		do {
			n = p->size & ~MARKBIT;
			++nblocks;
			nbytes += n;
			if (is_free(p)) {
				s = "free";
				++nblocksfree;
				nbytesfree += n;
			} else
				s = "used";
			if (dflag)
				printf("\t%X\t%d\t%s\n", p, n, s);
			check(p->size, succ(p)->losize);
			p = succ(p);
		} while (p != arena_end);
		++nblocks;			/* for arena_end block */
		nbytes += OVERHEAD;		/* for arena_end block */
		check(nbytes, (char *)arena_end - (char *)arena_start + OVERHEAD);
#if	ALLOC_STATS
		check(n_blocks, nblocks);
		check(n_bytes, nbytes);
		if (_add_free_called == 0) {
			check(n_blocks_free, nblocksfree);
			check(n_bytes_free, nbytesfree);
		}
#endif	/* ALLOC_STATS */
		if (dflag)
			putchar('\n');
	}

	/* Check the free list. */
	if (fflag)
		printf("Free list:\n");
	largest = nbytes = nblocks = 0;
	p = rover;
	check(p->prev->next, p);
	do {
		if (fflag)
			printf("\t%X\t%d\n", p, p->size);
		++nblocks;
		nbytes += p->size;
		if (p->size > largest)
			largest = p->size;
		check(p->next->prev, p);
		p = p->next;
	} while (p != rover);
	--nblocks;			/* do not count freelist0 */
#if	ALLOC_STATS
	if (_add_free_called == 0) {
		check(nblocks, n_blocks_free);
		check(nbytes, n_bytes_free);
	}
#endif	/* ALLOC_STATS */
	if (fflag)
		putchar('\n');
}
#endif	/* ALLOC_CHECK */

#if	ALLOC_STATS
/* Report statistics. */
void
FN_ALLOC_STATS(void)
{
	printf("_alloc_stats():\n");
	printf("sbrk():\t\t%d calls (%d failed)\n", n_calls_sbrk, n_calls_sbrk_failed);
	if (n_calls_calloc != 0)
		printf("calloc():\t%d calls\n", n_calls_calloc);
	if (n_calls_free != 0)
		printf("free():\t\t%d calls\n", n_calls_free);
	if (n_calls_malloc != 0)
		printf("malloc():\t%d calls\n", n_calls_malloc);
	if (n_calls_realloc != 0)
		printf("realloc():\t%d calls\n", n_calls_realloc);
	printf("\tTotal\tUsed\tFree\tUnallocated\n");
	printf("Blocks:\t%d\t%d\t%d\t%d\n",
	       n_blocks, n_blocks - n_blocks_free - n_blocks_unalloc, n_blocks_free, n_blocks_unalloc);
	printf("Bytes:\t%d\t%d\t%d\t%d\n\n", n_bytes, n_bytes - n_bytes_free -  n_bytes_unalloc, n_bytes_free, n_bytes_unalloc);
}
#endif	/* ALLOC_STATS */

/* Conditionalized out: cf. calloc.c. */
/* Allocate and clear memory. */
void *
FN_CALLOC(size_t nmemb, size_t size)
{
	void *FN_MALLOC(size_t size);
	void *s;

	alloc_stat(++n_calls_calloc);

	size *= nmemb;
	if ((s = FN_MALLOC(size)) == NULL)
		return NULL;
	memset(s, 0, size);
	return s;
}

/*
 * Free allocated memory.
 * Avoid fragmentation of the memory arena by joining all adjacent freed blocks.
 */
void
FN_FREE(void *ptr)
{
	BLOCK	*p, *q;
	size_t	n;

	alloc_stat(++n_calls_free);

	if (ptr == NULL)
		return;			/* ANSI says so */

	/* Make sure the block is currently allocated. */
	p = blockp(ptr);
	if (is_free(p)) {		/* block is not allocated */
#if	ALLOC_ERRORS
		fprintf(stderr, "free(0x%X): unallocated block\n", (uint)ptr);
		abort();		/* print message and die */
#else	/* !ALLOC_ERRORS */
		return;			/* ignore */
#endif	/* !ALLOC_ERRORS */
	}
	EXCL_START();
	clearmarks(p);			/* mark this block as free */

	/* Coalese with predecessor block if free. */
	if (is_predfree(p)) {
		/* Coalese this block with free predecessor block. */
		n = p->size;
		alloc_stat(--n_blocks);
		alloc_stat(n_bytes_free += n);
		p = pred(p);
		setsizes(p, p->size + n);
		delete(p);		/* delete p from the free list */
					/* (it gets put back again below...) */
	}

	/* Coalese with successor block if free. */
	q = succ(p);
	if (is_free(q)) {
		/* Coalese p with successor free block q. */
		alloc_stat(--n_blocks);
		setsizes(p, p->size + q->size);
		if (rover == q)
			rover = p;
		delete(q);		/* delete q from the free list */
	}
	add(p);				/* add p to freelist */
	EXCL_END();
}

/* Allocate memory. */
void *
FN_MALLOC(size_t size)
{
	BLOCK	*p, *q;
	size_t	m, n;

	alloc_stat(++n_calls_malloc);

	if (size == (size_t)0)
		return NULL;		/* implementation-defined behavior */

	/* Search the freelist for a big enough block. */
	EXCL_START();
	n = roundup(needed(size), ALIGNMENT);	/* needed memory block size */
	p = rover;
	do {
		if (p->size >= n)
			break;		/* block p is large enough */
		p = p->next;
	} while (p != rover);

	if (p->size < n) {
		EXCL_END();
		return NULL;		/* allocation failed */
	}

	/* Found or allocated a suitable free block p. */
	rover = p->next;
	m = p->size;
	if (m - n >= MINBLOCK) {
		/*
		 * Split block p into free and used parts.
		 * Rather than leaving the bottom block free
		 * and just leaving it on the free list,
		 * this leaves the top part free.  This requires an
		 * extra add() and delete(), but leaving the top part free
		 * helps avoid fragmentation when grow_arena() adds memory,
		 * because the top of the previous arena is often free.
		 */
		alloc_stat(++n_blocks);
		setsizes(p, n);
		q = succ(p);
		setsizes(q, m - n);
		alloc_stat(n_bytes_free -= m - n);
		add(q);
	}
	delete(p);		/* delete p from free list */
	setmarks(p);		/* mark p as used */
	EXCL_END();
	return (void *)memory(p);
}

/* Reallocate memory. */
void *
FN_REALLOC(void *ptr, size_t size)
{
	BLOCK	*p;
	size_t	old, new;
	void	*vp;

	alloc_stat(++n_calls_realloc);

	if (ptr == NULL)
		return FN_MALLOC(size);	/* ANSI says so */
	if (size == (size_t)0) {
		FN_FREE(ptr);		/* ANSI says so */
		return NULL;		/* implementation-defined */
	}

	/* Make sure the block is currently allocated. */
	p = blockp(ptr);
	if (is_free(p)) {		/* block is not allocated */
#if	ALLOC_ERRORS
		fprintf(stderr, "realloc(0x%X, %d): unallocated block\n", (uint)ptr, size);
		abort();		/* print message and die */
#else	/* !ALLOC_ERRORS */
		return NULL;		/* ignore */
#endif	/* !ALLOC_ERRORS */
	}

	EXCL_START();
	old = (p->size & ~MARKBIT);
	new = roundup(needed(size), ALIGNMENT);
	if (new <= old) {
		/* Shrink the block: either return unchanged or split it. */
		if (old - new < MINBLOCK) {
			EXCL_END();
			return ptr;	/* return block unchanged */
		}

		/* Shrink the block by splitting it. */
		alloc_stat(++n_blocks);
		setsizes(p, new);
		setmarks(p);
		p = succ(p);
		setsizes(p, old - new);
		add(p);
		EXCL_END();
		return ptr;
	} else {
		/* Grow the block. */
		/* N.B. Could check if enough space in start of next block... */
		EXCL_END();
		if ((vp = FN_MALLOC(size)) == NULL)
			return NULL;
		memcpy(vp, ptr, old - OVERHEAD);
		free(ptr);
		return vp;
	}
}

/* end of malloc.c */
