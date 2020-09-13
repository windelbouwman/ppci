
#ifndef _LIBC_LIMITS_H_
#define _LIBC_LIMITS_H_

#define CHAR_BIT 8

#define SCHAR_MIN (-128)
#define SCHAR_MAX 127

#define UCHAR_MAX 255

#define CHAR_MIN 0
#define CHAR_MAX UCHAR_MAX

#define SHRT_MIN (-32768)
#define SHRT_MAX 32767

#define USHRT_MAX 65535

#define INT_MIN -2147483648
#define INT_MAX 2147483647
#define UINT_MAX 4294967295

// TODO: those values depend upon machine width .. :(
#define LONG_MIN -9223372036854775808
#define LONG_MAX 9223372036854775807
#define ULONG_MAX 18446744073709551615

// This is a controversial define:
#define PATH_MAX 4096

#endif
