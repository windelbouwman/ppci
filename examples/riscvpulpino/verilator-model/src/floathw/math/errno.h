/*
 * errno.h
 * Errors.
 * ANSI/ISO 9899-1990, Section 7.1.4.
 */

#ifndef __ERRNO_H__
#define __ERRNO_H__

#if	defined(__cplusplus)
extern	"C"	{
#endif	/* defined(__cplusplus) */

extern int errno;

/*
 * Macros.
 * Only EDOM and ERANGE are required by ANSI/ISO 9899-1990.
 * Other values defined here are required by Posix.1
 * (ISO/IEC 9945-1:1990, a.k.a. IEEE 1003.1-1990), except:
 * ENOTBLK and ETXTBSY are defined here but not in Posix.1, and
 * EDEADLK, ENOLCK, ENOTEMPTY, ENOSYS are in Posix.1.
 * Error number values 1-34 are fairly standard across different hosts,
 * while values 35 and up vary widely.
 */
#define	EPERM		 1		/* Operation not permitted	*/
#define	ENOENT		 2		/* No such file or directory	*/
#define	ESRCH		 3		/* No such process		*/
#define	EINTR		 4		/* Interrupted function call	*/
#define	EIO		 5		/* Input/output error		*/
#define	ENXIO		 6		/* No such device or address	*/
#define	E2BIG		 7		/* Arg list too long		*/
#define	ENOEXEC		 8		/* Exec format error		*/
#define	EBADF		 9		/* Bad file descriptor		*/
#define	ECHILD		10		/* No child processes		*/
#define	EAGAIN		11		/* Resource temporarily unavailable */
#define	ENOMEM		12		/* Not enough space		*/
#define	EACCES		13		/* Permission denied		*/
#define	EFAULT		14		/* Bad address			*/
#define	ENOTBLK		15		/* Block device required	*/
#define	EBUSY		16		/* Resource busy		*/
#define	EEXIST		17		/* File exists			*/
#define	EXDEV		18		/* Improper link		*/
#define	ENODEV		19		/* No such device		*/
#define	ENOTDIR		20		/* Not a directory		*/
#define	EISDIR		21		/* Is a directory		*/
#define	EINVAL		22		/* Invalid argument		*/
#define	ENFILE		23		/* Too many open files in system */
#define	EMFILE		24		/* Too many open files		*/
#define	ENOTTY		25		/* Inappropriate I/O control operation */
#define	ETXTBSY		26		/* Text file busy		*/
#define	EFBIG		27		/* File too large		*/
#define	ENOSPC		28		/* No space left on device	*/
#define	ESPIPE		29		/* Invalid seek			*/
#define	EROFS		30		/* Read-only file system	*/
#define	EMLINK		31		/* Too many links		*/
#define	EPIPE		32		/* Broken pipe			*/
#define	EDOM		33		/* Domain error			*/
#define	ERANGE		34		/* Result too large		*/
#define	ENAMETOOLONG	35		/* Filename too long		*/

#define EDEADLK		36		/* Resource deadlock avoided    */
#define ENOLCK		37		/* No locks available 		*/
#define ENOTEMPTY	38		/* Directory not empty		*/
#define ENOSYS		39		/* Function not implemented     */

/* Internals. */
#define	_STRERROR_MAX	36		/* max length of strerror() result */
extern	const	char	 _sys_errformat[];
extern	const	char	*_sys_errlist[];
extern	const	unsigned _sys_nerr;

#if	defined(__cplusplus)
}
#endif	/* defined(__cplusplus) */

#endif	/* __ERRNO_H__ */

/* end of errno.h */
