#ifndef STDIO_H
#define STDIO_H

#include <stdlib.h>

void printf(char*, ...);
extern void bsp_putc(char);

int sprintf(char* str, const char* format, ...);

typedef int FILE;

FILE* fopen(const char* filename, const char* mode);
fclose(FILE* stream);

#endif

