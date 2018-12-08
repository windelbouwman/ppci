#ifndef STDINT_H_PPCI
#define STDINT_H_PPCI

// In case of hosted C compilation, take stdint from c library:
#if __STDC_HOSTED__
#include_next <stdint.h>
#else
// In case of free standing C compilation, take these defines:

// See also: http://www.cplusplus.com/reference/cstdint/

// Exact width:
typedef char int8_t;
typedef unsigned char uint8_t;

typedef short int16_t;
typedef unsigned short uint16_t;

typedef int int32_t;
typedef unsigned int uint32_t;

typedef int int64_t;
typedef unsigned int uint64_t;

// Least:
typedef char int_least8_t;
typedef unsigned char uint_least8_t;

typedef short int_least16_t;
typedef unsigned short uint_least16_t;

typedef int int_least32_t;
typedef unsigned int uint_least32_t;

typedef int int_least64_t;
typedef unsigned int uint_least64_t;

// Fast:
typedef char int_fast8_t;
typedef unsigned char uint_fast8_t;

typedef short int_fast16_t;
typedef unsigned short uint_fast16_t;

typedef int int_fast32_t;
typedef unsigned int uint_fast32_t;

typedef int int_fast64_t;
typedef unsigned int uint_fast64_t;

// Pointers:
typedef unsigned int intptr_t;
typedef unsigned int uintptr_t;

#endif

#endif
