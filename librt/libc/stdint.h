#ifndef STDINT_H_PPCI
#define STDINT_H_PPCI

// In case of hosted C compilation, take stdint from c library:
#if __STDC_HOSTED__
#include_next <stdint.h>
#else
// In case of free standing C compilation, take these defines:
typedef char int8_t;
typedef unsigned char uint8_t;

typedef short int16_t;
typedef unsigned short uint16_t;

typedef int int32_t;
typedef unsigned int uint32_t;
#endif

#endif
