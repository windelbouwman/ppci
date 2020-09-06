
#ifndef UNISTD_H
#define UNISTD_H

#include <stddef.h>

int isatty(int fd);
char *getcwd(char *buf, size_t size);
char *getwd(char *buf);

#endif

