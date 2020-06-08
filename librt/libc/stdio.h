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
int feof(FILE* stream);
int fileno(FILE* stream);

// Formatted output:
int fprintf(FILE*stream, const char* format, ...);
int sprintf(char* str, const char* format, ...);
int printf(const char *fornat, ...);
int sprintf(char* str, const char*, ...);
int snprintf(char* str, size_t n, const char *format, ...);
int vprintf(const char * format, va_list arg);
int vsnprintf(char* str, size_t n, const char *format, va_list arg);
int vsprintf(char* str, const char*, va_list arg);
int vfprintf(FILE* stream, const char * format, va_list arg);

extern FILE *stdin;
extern FILE *stdout;
extern FILE *stderr;

// Character IO:
int fgetc(FILE* stream);
#define getc fgetc
int fputc(int character, FILE* stream);
#define putc fputc
char* fgets(char* str, int num, FILE* stream);
int fputs(const char* str, FILE* stream);
int ungetc(int character, FILE* stream);

// direct IO:
size_t fread(void * ptr, size_t size, size_t count, FILE* stream);
size_t fwrite(const void* ptr, size_t size, size_t count, FILE* stream);
int fseek(FILE* stream, long int offset, int origin);

#define EOF (-1)

// Low level functions:

int putchar(int character);
int getchar(void);

#endif

