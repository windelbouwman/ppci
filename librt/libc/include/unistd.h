
#ifndef UNISTD_H
#define UNISTD_H

#include "stddef.h"

int isatty(int fd);
char *getcwd(char *buf, size_t size);
char *getwd(char *buf);

ssize_t read(int, void *, size_t);
ssize_t write(int, const void *, size_t);

int close(int);

#endif

