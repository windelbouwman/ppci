#ifndef STDIO_H
#define STDIO_H

#include "stdlib.h"
#include "stdarg.h"
// See also: http://www.cplusplus.com/reference/cstdio/

// Mantaining this function for tests sake
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
int printf(const char *format, ...);
int sprintf(char* str, const char* format, ...);
int snprintf(char* str, size_t n, const char *format, ...);	
int vprintf(const char * format, va_list arg);	
int vsnprintf(char* str, size_t n, const char *format, va_list arg);	
int vsprintf(char* str, const char*, va_list arg);
int vfprintf(FILE* stream, const char * format, va_list arg);

extern FILE *stdin;
extern FILE *stdout;
extern FILE *stderr;

// Character IO:
int putc(int character, FILE* stream);
//void puts(char *s);
char getc();
int fgetc(FILE* stream);
int fputc(int character, FILE* stream);
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
