/*
 * lib-src/ansi/errno/errno.c
 * ANSI/ISO 9899-1990, Section 7.1.3.
 *
 * int errno;
 *
 * The global definition of errno is initialized with an explicit 0 here
 * so that LifeLib does not issue pages of warnings
 * about extern resolving to a common.
 */


#include <errno.h>

int errno = 0;
