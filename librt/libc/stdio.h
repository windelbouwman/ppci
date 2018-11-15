#ifndef STDIO_H
#define STDIO_H

#include <stdlib.h>
#include <stdarg.h>
// See also: http://www.cplusplus.com/reference/cstdio/

extern void bsp_putc(char);


typedef int FILE;

// File access:
FILE* fopen(const char* filename, const char* mode);
int fflush(FILE* stream);
int fclose(FILE* stream);

// Formatted output:
int fprintf(FILE*stream, const char* format, ...);
int sprintf(char* str, const char* format, ...);
int printf(const char *fornat, ...);
int sprintf(char* str, const char*, ...);
int snprintf(char* str, size_t n, const char *format, ...);
int vsnprintf(char* str, size_t n, const char *format, va_list arg);
int vsprintf(char* str, const char*, va_list arg);

extern FILE *stdin;
extern FILE *stdout;
extern FILE *stderr;

#endif

