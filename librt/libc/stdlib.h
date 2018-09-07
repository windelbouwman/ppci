#ifndef STDLIB_H
#define STDLIB_H

typedef unsigned int size_t;

// Memory
void* malloc(size_t size);
void* calloc(size_t num, size_t size);
void free(void* ptr);

void abort(void);

#endif
