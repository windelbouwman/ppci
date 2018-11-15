#ifndef STRING_H
#define STRING_H

#include <stdlib.h>

/*
 * See also: http://www.cplusplus.com/reference/cstring/
 *
 */

// Copying:
void* memcpy(void* destination, const void* source, size_t num);
void* memmove(void* destination, const void* source, size_t num);
char* strcpy(char* destination, const char* source);
char* strncpy(char* destination, const char* source, size_t num);

// Concatenation:
char* strcat(char* destination, const char* source);

// Comparison:

int memcmp(const void* ptr1, const void* ptr2, size_t num);
int strcmp(const char* str1, const char* str2);
int strncmp(const char* str1, const char* str2, size_t num);

// Other:
void* memset(void* ptr, int value, size_t num);
size_t strlen(const char* str);
#endif
